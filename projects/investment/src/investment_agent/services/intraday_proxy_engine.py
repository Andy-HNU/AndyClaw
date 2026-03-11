from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from investment_agent.models.portfolio import PortfolioState


DEFAULT_SENTIMENT_THRESHOLDS: dict[str, float] = {
    "panic_price_trend_max": -2.0,
    "panic_volume_ratio_min": 1.6,
    "panic_drawdown_max": -1.6,
    "washout_amplitude_min": 3.0,
    "washout_volume_ratio_min": 1.35,
    "washout_close_position_max": 0.62,
    "range_price_abs_max": 0.9,
    "range_volume_ratio_max": 1.2,
    "range_volume_ratio_min": 0.85,
    "range_amplitude_max": 2.2,
    "drift_down_price_trend_max": -0.55,
    "drift_down_volume_ratio_max": 0.9,
    "rebound_price_trend_min": 0.45,
    "rebound_volume_ratio_max": 0.95,
    "breakout_price_trend_min": 1.4,
    "breakout_volume_ratio_min": 1.5,
    "breakout_close_position_min": 0.78,
    "breakout_distance_min": 0.45,
    "stall_price_trend_min": 0.9,
    "stall_close_position_min": 0.25,
    "stall_drawdown_max": -0.85,
    "stall_volume_ratio_max": 1.15,
    "chase_price_trend_min": 1.2,
    "chase_volume_ratio_min": 1.35,
    "chase_drawdown_min": -1.0,
    "chase_close_position_min": 0.7,
    "neutral_price_abs_max": 0.2,
    "neutral_amplitude_max": 0.6,
    "neutral_volume_gap_max": 0.08,
}


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


def _derive_close_position_in_range(drawdown_pct: float, amplitude_pct: float) -> float:
    if amplitude_pct <= 0:
        return 0.5
    position = 1.0 + drawdown_pct / amplitude_pct
    return max(0.0, min(1.0, position))


def _derive_support_resistance_levels(
    proxy_nav_now: float,
    metrics: dict[str, float],
    thresholds: dict[str, Any],
) -> dict[str, Any]:
    amplitude_pct = max(float(metrics.get("amplitude_pct", 0.0)), 0.0)
    range_factor = max(amplitude_pct / 100, 0.003)
    support = proxy_nav_now * (1 - range_factor * 0.45)
    resistance = proxy_nav_now * (1 + range_factor * 0.55)
    breakout_buffer = max(float(thresholds.get("breakout_distance_min", 0.45)) / 100, 0.003)
    breakout = resistance * (1 + breakout_buffer)
    return {
        "support_level": round(support, 4),
        "resistance_level": round(resistance, 4),
        "breakout_level": round(breakout, 4),
        "level_basis": {
            "method": "intraday_range_band",
            "range_factor": round(range_factor, 6),
            "breakout_buffer": round(breakout_buffer, 6),
            "window": "intraday_session",
        },
    }


def _build_unavailable_fund(fund_code: str, fund_name: str, reason: str, data_quality: str) -> dict[str, Any]:
    return {
        "fund_code": fund_code,
        "fund_name": fund_name,
        "status": "unavailable",
        "reason": reason,
        "proxy_nav_now": None,
        "expected_close_band": None,
        "support_level": None,
        "resistance_level": None,
        "breakout_level": None,
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


def classify_intraday_sentiment(
    metrics: dict[str, Any],
    thresholds: dict[str, Any] | None = None,
) -> dict[str, Any]:
    price_trend = float(metrics.get("price_trend_pct", 0.0))
    volume_ratio = float(metrics.get("volume_ratio", 1.0))
    amplitude_pct = float(metrics.get("amplitude_pct", 0.0))
    drawdown_pct = float(metrics.get("drawdown_from_high_pct", 0.0))
    close_position = _derive_close_position_in_range(drawdown_pct, amplitude_pct)
    active_thresholds = {**DEFAULT_SENTIMENT_THRESHOLDS, **(thresholds or {})}
    breakout_distance_pct = max(0.0, price_trend - float(active_thresholds["range_price_abs_max"]))

    label = "intraday_neutral_observe"
    probability = 0.42
    wording = "盘中证据不足，先按中性观察处理。"
    suggested_action = "继续观察量价配合，暂不做方向性动作。"
    matched_rules = ["insufficient_evidence"]

    if (
        abs(price_trend) <= float(active_thresholds["neutral_price_abs_max"])
        and amplitude_pct <= float(active_thresholds["neutral_amplitude_max"])
        and abs(volume_ratio - 1.0) <= float(active_thresholds["neutral_volume_gap_max"])
    ):
        label = "intraday_neutral_observe"
        probability = 0.66
        wording = "盘中波动很小，暂无明确方向优势。"
        suggested_action = "保持观察，等待有效突破或放量转弱。"
        matched_rules = ["narrow_price_action", "flat_volume"]
    elif (
        price_trend <= float(active_thresholds["panic_price_trend_max"])
        and volume_ratio >= float(active_thresholds["panic_volume_ratio_min"])
        and drawdown_pct <= float(active_thresholds["panic_drawdown_max"])
    ):
        label = "intraday_panic_selloff"
        probability = min(0.94, 0.62 + abs(price_trend) * 0.08 + max(volume_ratio - 1.0, 0.0) * 0.1)
        wording = "盘中偏恐慌踩踏，抛压释放仍未结束。"
        suggested_action = "优先控仓，等待跌势放缓后再评估。"
        matched_rules = ["price_breakdown", "heavy_volume", "deep_drawdown"]
    elif (
        price_trend >= float(active_thresholds["breakout_price_trend_min"])
        and volume_ratio >= float(active_thresholds["breakout_volume_ratio_min"])
        and close_position >= float(active_thresholds["breakout_close_position_min"])
        and breakout_distance_pct >= float(active_thresholds["breakout_distance_min"])
    ):
        label = "intraday_volume_breakout"
        probability = min(0.92, 0.6 + price_trend * 0.07 + max(volume_ratio - 1.0, 0.0) * 0.12)
        wording = "盘中偏放量突破，资金正在尝试抬升定价中枢。"
        suggested_action = "可小步跟随，若跌回突破位下方应及时降速。"
        matched_rules = ["breakout_trend", "volume_expansion", "strong_close_position"]
    elif (
        price_trend >= float(active_thresholds["chase_price_trend_min"])
        and volume_ratio >= float(active_thresholds["chase_volume_ratio_min"])
        and drawdown_pct >= float(active_thresholds["chase_drawdown_min"])
        and close_position >= float(active_thresholds["chase_close_position_min"])
    ):
        label = "intraday_momentum_chase"
        probability = min(0.9, 0.56 + price_trend * 0.09 + max(volume_ratio - 1.0, 0.0) * 0.08)
        wording = "盘中偏情绪高涨追涨，短线热度较高。"
        suggested_action = "不宜追高，等回踩承接后再考虑跟随。"
        matched_rules = ["positive_trend", "volume_confirmation", "high_close_position"]
    elif (
        amplitude_pct >= float(active_thresholds["washout_amplitude_min"])
        and volume_ratio >= float(active_thresholds["washout_volume_ratio_min"])
        and close_position <= float(active_thresholds["washout_close_position_max"])
    ):
        label = "intraday_distribution_or_washout"
        probability = min(0.88, 0.54 + amplitude_pct * 0.05 + max(volume_ratio - 1.0, 0.0) * 0.08)
        wording = "盘中偏分歧洗盘，资金拉扯较明显。"
        suggested_action = "减少追单，等待尾盘方向确认再处理。"
        matched_rules = ["wide_range", "elevated_volume", "weak_close_shape"]
    elif (
        price_trend <= float(active_thresholds["drift_down_price_trend_max"])
        and volume_ratio <= float(active_thresholds["drift_down_volume_ratio_max"])
    ):
        label = "intraday_low_volume_drift_down"
        probability = min(0.82, 0.5 + abs(price_trend) * 0.1 + max(1.0 - volume_ratio, 0.0) * 0.2)
        wording = "盘中偏缩量阴跌，趋势走弱但情绪不极端。"
        suggested_action = "降低进攻仓位，等量价改善再考虑加仓。"
        matched_rules = ["negative_trend", "low_volume"]
    elif (
        price_trend >= float(active_thresholds["rebound_price_trend_min"])
        and volume_ratio <= float(active_thresholds["rebound_volume_ratio_max"])
    ):
        label = "intraday_low_volume_rebound"
        probability = min(0.8, 0.5 + price_trend * 0.09 + max(1.0 - volume_ratio, 0.0) * 0.18)
        wording = "盘中偏缩量反弹，修复力度仍需观察。"
        suggested_action = "先当修复看待，放量前不宜激进追涨。"
        matched_rules = ["positive_trend", "rebound_without_volume"]
    elif (
        price_trend >= float(active_thresholds["stall_price_trend_min"])
        and close_position >= float(active_thresholds["stall_close_position_min"])
        and drawdown_pct <= float(active_thresholds["stall_drawdown_max"])
        and volume_ratio <= float(active_thresholds["stall_volume_ratio_max"])
    ):
        label = "intraday_high_level_stall"
        probability = min(0.83, 0.5 + price_trend * 0.06 + abs(drawdown_pct) * 0.06)
        wording = "盘中偏高位滞涨，冲高后承接并不充分。"
        suggested_action = "加仓节奏放慢，防范冲高回落。"
        matched_rules = ["high_level", "weak_follow_through", "intraday_pullback"]
    elif (
        abs(price_trend) <= float(active_thresholds["range_price_abs_max"])
        and float(active_thresholds["range_volume_ratio_min"]) <= volume_ratio <= float(active_thresholds["range_volume_ratio_max"])
        and amplitude_pct <= float(active_thresholds["range_amplitude_max"])
    ):
        label = "intraday_range_chop"
        probability = 0.62
        wording = "盘中偏区间震荡，尚未形成明确突破方向。"
        suggested_action = "继续观望，等待区间突破并确认量能。"
        matched_rules = ["sideways_trading", "balanced_volume"]

    confidence_score = round(max(0.35, min(0.95, probability)), 4)
    return {
        "label": label,
        "probability": round(probability, 4),
        "confidence_score": confidence_score,
        "wording": wording,
        "suggested_action": suggested_action,
        "evidence": {
            "price_trend_pct": round(price_trend, 4),
            "volume_ratio": round(volume_ratio, 4),
            "amplitude_pct": round(amplitude_pct, 4),
            "drawdown_from_high_pct": round(drawdown_pct, 4),
            "close_position_in_range": round(close_position, 4),
            "breakout_distance_pct": round(breakout_distance_pct, 4),
            "matched_rules": matched_rules,
            "confidence_score": confidence_score,
            "thresholds": active_thresholds,
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
    realtime_path: Path | None = None,
    realtime_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    config_payload = load_intraday_proxy_config(config_path)
    funds_config = dict(config_payload.get("funds") or {})
    sentiment_thresholds = dict(config_payload.get("sentiment_thresholds") or {})
    assets_by_symbol = {str(asset.symbol): asset for asset in portfolio_state.assets if asset.symbol}
    mapped_fund_codes = [
        str(asset.symbol)
        for asset in portfolio_state.assets
        if asset.symbol and str(asset.symbol) in funds_config
    ]

    if realtime_payload is None:
        if realtime_path is None or not Path(realtime_path).exists():
            funds = [
                _build_unavailable_fund(
                    fund_code=fund_code,
                    fund_name=str(funds_config.get(fund_code, {}).get("fund_name") or fund_code),
                    reason="realtime_feed_missing",
                    data_quality="fallback",
                )
                for fund_code in mapped_fund_codes
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
            for fund_code in mapped_fund_codes
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

    for fund_code in mapped_fund_codes:
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
        levels = _derive_support_resistance_levels(proxy_nav_now, metrics, sentiment_thresholds)
        sentiment = classify_intraday_sentiment(metrics, sentiment_thresholds)
        funds.append(
            {
                "fund_code": fund_code,
                "fund_name": fund_name,
                "asset_code": asset.theme or asset.name,
                "status": "available",
                "proxy_method": proxy_method,
                "proxy_nav_now": round(proxy_nav_now, 4),
                "expected_close_band": expected_close_band,
                "support_level": levels["support_level"],
                "resistance_level": levels["resistance_level"],
                "breakout_level": levels["breakout_level"],
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
                    "support_resistance_basis": levels["level_basis"],
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
