from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from investment_agent.models.portfolio import PortfolioState


SUPPORTED_FUNDS = ("012734", "011609")


def _round_or_none(value: float | None, digits: int = 4) -> float | None:
    if value is None:
        return None
    return round(value, digits)


def _sum_weights(drivers: list[dict[str, Any]]) -> float:
    return sum(float(item.get("weight", 0.0)) for item in drivers)


def _normalize_drivers(drivers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    total_weight = _sum_weights(drivers)
    if total_weight <= 0:
        return []
    normalized: list[dict[str, Any]] = []
    for item in drivers:
        normalized.append({**item, "weight": float(item["weight"]) / total_weight})
    return normalized


def _confidence_label(score: float) -> str:
    if score >= 0.75:
        return "高"
    if score >= 0.5:
        return "中"
    return "低"


def _volume_state(volume_ratio: float) -> str:
    if volume_ratio >= 1.8:
        return "放量明显"
    if volume_ratio >= 1.2:
        return "温和放量"
    if volume_ratio >= 0.85:
        return "量能平稳"
    return "缩量"


def _build_unavailable_fund(fund_code: str, fund_name: str, reason: str, data_quality: str) -> dict[str, Any]:
    return {
        "fund_code": fund_code,
        "fund_name": fund_name,
        "status": "unavailable",
        "reason": reason,
        "proxy_nav_now": None,
        "expected_close_band": None,
        "volume_state": "不可用",
        "sentiment_label": "intraday_unavailable",
        "confidence": {"score": 0.0, "label": "低"},
        "suggested_action": "等待实时数据恢复后再判断",
        "driver_breakdown": [],
        "evidence": {"reason": reason},
        "data_quality": data_quality,
    }


def load_intraday_proxy_config(path: Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return dict(payload)


def load_intraday_realtime_feed(path: Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return dict(payload)


def classify_intraday_sentiment(metrics: dict[str, Any]) -> dict[str, Any]:
    price_trend = float(metrics.get("price_trend_pct", 0.0))
    volume_ratio = float(metrics.get("volume_ratio", 1.0))
    amplitude_pct = float(metrics.get("amplitude_pct", 0.0))
    drawdown_pct = float(metrics.get("drawdown_from_high_pct", 0.0))

    label = "intraday_range_chop"
    probability = 0.52
    wording = "盘中更像区间震荡，暂时缺少单边定价证据。"
    suggested_action = "以观察为主，等待方向确认。"
    matched_rules = ["baseline_range"]

    if price_trend <= -2.0 and volume_ratio >= 1.6 and drawdown_pct <= -1.6:
        label = "intraday_panic_selloff"
        probability = min(0.92, 0.58 + abs(price_trend) * 0.08 + max(volume_ratio - 1.0, 0.0) * 0.12)
        wording = "盘中更像恐慌性抛售，尾盘仍可能继续放大波动。"
        suggested_action = "避免逆势加仓，优先等待抛压缓和。"
        matched_rules = ["price_breakdown", "heavy_volume", "deep_drawdown"]
    elif amplitude_pct >= 3.0 and volume_ratio >= 1.35 and (price_trend <= -0.8 or drawdown_pct <= -1.2):
        label = "intraday_distribution_or_washout"
        probability = min(0.86, 0.55 + amplitude_pct * 0.05 + max(volume_ratio - 1.0, 0.0) * 0.08)
        wording = "盘中更像派发或洗盘，方向尚未完全确认。"
        suggested_action = "控制追单，等待尾盘资金回流或跌幅收敛。"
        matched_rules = ["wide_range", "elevated_volume", "weak_close_shape"]
    elif price_trend >= 1.2 and volume_ratio >= 1.35 and drawdown_pct >= -1.0:
        label = "intraday_momentum_chase"
        probability = min(0.88, 0.53 + price_trend * 0.09 + max(volume_ratio - 1.0, 0.0) * 0.07)
        wording = "盘中更像资金追涨，后续要防止高位回吐。"
        suggested_action = "不追高，等尾盘确认承接再决定。"
        matched_rules = ["positive_trend", "volume_confirmation", "shallow_pullback"]

    return {
        "label": label,
        "probability": round(probability, 4),
        "wording": wording,
        "suggested_action": suggested_action,
        "evidence": {
            "price_trend_pct": round(price_trend, 4),
            "volume_ratio": round(volume_ratio, 4),
            "amplitude_pct": round(amplitude_pct, 4),
            "drawdown_from_high_pct": round(drawdown_pct, 4),
            "matched_rules": matched_rules,
        },
    }


def _resolve_reference_nav(asset: Any, config_item: dict[str, Any]) -> float | None:
    if asset.shares:
        return float(asset.value) / float(asset.shares)
    if config_item.get("reference_nav") is not None:
        return float(config_item["reference_nav"])
    return None


def _build_driver_breakdown(
    configured_drivers: list[dict[str, Any]],
    realtime_by_code: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], float]:
    raw_drivers: list[dict[str, Any]] = []
    covered_weight = 0.0
    for configured in configured_drivers:
        driver_code = str(configured["driver_code"])
        driver_realtime = realtime_by_code.get(driver_code)
        if driver_realtime is None:
            continue
        weight = float(configured["weight"])
        covered_weight += weight
        price_change_pct = float(driver_realtime["price_change_pct"])
        raw_drivers.append(
            {
                "driver_code": driver_code,
                "driver_name": str(configured.get("driver_name") or driver_realtime.get("driver_name") or driver_code),
                "weight": weight,
                "price_change_pct": round(price_change_pct, 4),
                "contribution_pct": round(weight * price_change_pct, 4),
                "volume_ratio": _round_or_none(float(driver_realtime["volume_ratio"]))
                if driver_realtime.get("volume_ratio") is not None
                else None,
                "amplitude_pct": _round_or_none(float(driver_realtime["amplitude_pct"]))
                if driver_realtime.get("amplitude_pct") is not None
                else None,
                "drawdown_from_high_pct": _round_or_none(float(driver_realtime["drawdown_from_high_pct"]))
                if driver_realtime.get("drawdown_from_high_pct") is not None
                else None,
            }
        )
    normalized = _normalize_drivers(raw_drivers)
    for item in normalized:
        item["weight"] = round(float(item["weight"]), 4)
        item["contribution_pct"] = round(item["weight"] * float(item["price_change_pct"]), 4)
    return normalized, round(covered_weight, 4)


def _aggregate_metrics(driver_breakdown: list[dict[str, Any]]) -> dict[str, float]:
    if not driver_breakdown:
        return {
            "price_trend_pct": 0.0,
            "volume_ratio": 1.0,
            "amplitude_pct": 0.0,
            "drawdown_from_high_pct": 0.0,
        }
    price_trend = sum(float(item["weight"]) * float(item["price_change_pct"]) for item in driver_breakdown)
    volume_ratio = sum(float(item["weight"]) * float(item.get("volume_ratio") or 1.0) for item in driver_breakdown)
    amplitude_pct = sum(float(item["weight"]) * float(item.get("amplitude_pct") or 0.0) for item in driver_breakdown)
    drawdown_pct = sum(
        float(item["weight"]) * float(item.get("drawdown_from_high_pct") or 0.0) for item in driver_breakdown
    )
    return {
        "price_trend_pct": round(price_trend, 4),
        "volume_ratio": round(volume_ratio, 4),
        "amplitude_pct": round(amplitude_pct, 4),
        "drawdown_from_high_pct": round(drawdown_pct, 4),
    }


def build_intraday_proxy_review(
    portfolio_state: PortfolioState,
    config_path: Path,
    realtime_path: Path,
) -> dict[str, Any]:
    config_payload = load_intraday_proxy_config(config_path)
    funds_config = dict(config_payload.get("funds") or {})
    assets_by_symbol = {str(asset.symbol): asset for asset in portfolio_state.assets if asset.symbol}

    if not Path(realtime_path).exists():
        funds = [
            _build_unavailable_fund(
                fund_code=fund_code,
                fund_name=str(funds_config.get(fund_code, {}).get("fund_name") or fund_code),
                reason="realtime_feed_missing",
                data_quality="fallback",
            )
            for fund_code in SUPPORTED_FUNDS
            if fund_code in funds_config
        ]
        return {
            "status": "unavailable",
            "reason": "realtime_feed_missing",
            "data_quality": "fallback",
            "as_of": None,
            "funds": funds,
        }

    realtime_payload = load_intraday_realtime_feed(realtime_path)
    if str(realtime_payload.get("status", "success")) != "success":
        reason = str(realtime_payload.get("reason") or "realtime_feed_unavailable")
        funds = [
            _build_unavailable_fund(
                fund_code=fund_code,
                fund_name=str(funds_config.get(fund_code, {}).get("fund_name") or fund_code),
                reason=reason,
                data_quality=str(realtime_payload.get("data_quality") or "fallback"),
            )
            for fund_code in SUPPORTED_FUNDS
            if fund_code in funds_config
        ]
        return {
            "status": "unavailable",
            "reason": reason,
            "data_quality": str(realtime_payload.get("data_quality") or "fallback"),
            "as_of": realtime_payload.get("as_of"),
            "funds": funds,
        }

    realtime_by_code = {
        str(item["driver_code"]): dict(item)
        for item in realtime_payload.get("drivers", [])
    }
    data_quality = str(realtime_payload.get("data_quality") or "mixed")
    funds: list[dict[str, Any]] = []

    for fund_code in SUPPORTED_FUNDS:
        config_item = funds_config.get(fund_code)
        if config_item is None:
            continue
        asset = assets_by_symbol.get(fund_code)
        fund_name = str(config_item.get("fund_name") or (asset.name if asset is not None else fund_code))
        if asset is None:
            funds.append(_build_unavailable_fund(fund_code, fund_name, "fund_not_in_portfolio", data_quality))
            continue

        proxy_method = "fallback_mapping"
        breakdown, covered_weight = _build_driver_breakdown(
            list(config_item.get("holdings", [])),
            realtime_by_code,
        )
        if breakdown and covered_weight >= float(config_item.get("minimum_holdings_coverage", 0.5)):
            proxy_method = "holdings"
        else:
            breakdown, covered_weight = _build_driver_breakdown(
                list(config_item.get("fallback_mapping", [])),
                realtime_by_code,
            )

        if not breakdown:
            funds.append(_build_unavailable_fund(fund_code, fund_name, "realtime_driver_missing", data_quality))
            continue

        reference_nav = _resolve_reference_nav(asset, config_item)
        if reference_nav is None:
            funds.append(_build_unavailable_fund(fund_code, fund_name, "reference_nav_missing", data_quality))
            continue

        metrics = _aggregate_metrics(breakdown)
        proxy_change_pct = float(metrics["price_trend_pct"])
        proxy_nav_now = reference_nav * (1 + proxy_change_pct / 100)
        uncertainty_pct = (
            float(config_item.get("base_band_pct", 0.0045))
            + float(metrics["amplitude_pct"]) / 100 * 0.16
            + abs(min(float(metrics["drawdown_from_high_pct"]), 0.0)) / 100 * 0.12
        )
        expected_close_band = {
            "low": round(proxy_nav_now * (1 - uncertainty_pct), 4),
            "high": round(proxy_nav_now * (1 + uncertainty_pct), 4),
        }
        confidence_score = min(
            0.95,
            0.35
            + covered_weight * 0.4
            + min(len(breakdown), 3) * 0.08
            + (0.08 if proxy_method == "holdings" else 0.0),
        )
        sentiment = classify_intraday_sentiment(metrics)
        funds.append(
            {
                "fund_code": fund_code,
                "fund_name": fund_name,
                "asset_code": asset.theme or asset.name,
                "status": "available",
                "proxy_method": proxy_method,
                "proxy_nav_now": round(proxy_nav_now, 4),
                "expected_close_band": expected_close_band,
                "price_trend_pct": round(proxy_change_pct, 4),
                "volume_state": _volume_state(float(metrics["volume_ratio"])),
                "sentiment_label": sentiment["label"],
                "sentiment_wording": sentiment["wording"],
                "confidence": {
                    "score": round(confidence_score, 4),
                    "label": _confidence_label(confidence_score),
                },
                "suggested_action": str(sentiment["suggested_action"]),
                "driver_breakdown": breakdown,
                "evidence": {
                    **sentiment["evidence"],
                    "proxy_method": proxy_method,
                    "holdings_coverage": round(covered_weight, 4),
                    "reference_nav": round(reference_nav, 4),
                },
                "data_quality": data_quality,
            }
        )

    overall_status = "available" if any(item["status"] == "available" for item in funds) else "unavailable"
    return {
        "status": overall_status,
        "reason": None if overall_status == "available" else "realtime_feed_unavailable",
        "data_quality": data_quality,
        "as_of": realtime_payload.get("as_of"),
        "funds": funds,
    }
