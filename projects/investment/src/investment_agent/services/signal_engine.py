from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from investment_agent.models.portfolio import Asset, PortfolioState


@dataclass(frozen=True)
class PriceBar:
    close: float
    high: float
    low: float
    volume: float

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "PriceBar":
        return cls(
            close=float(payload["close"]),
            high=float(payload["high"]),
            low=float(payload["low"]),
            volume=float(payload["volume"]),
        )


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def sma(values: list[float], window: int) -> float:
    subset = values[-min(len(values), window) :]
    return mean(subset)


def compute_drawdown_pct(values: list[float], window: int) -> float:
    subset = values[-min(len(values), window) :]
    if not subset:
        return 0.0
    peak = max(subset)
    if peak == 0:
        return 0.0
    return round(((subset[-1] - peak) / peak) * 100, 4)


def compute_ad_line(bars: list[PriceBar]) -> list[float]:
    line: list[float] = []
    current = 0.0
    for bar in bars:
        if math.isclose(bar.high, bar.low):
            multiplier = 0.0
        else:
            multiplier = ((bar.close - bar.low) - (bar.high - bar.close)) / (bar.high - bar.low)
        current += multiplier * bar.volume
        line.append(round(current, 4))
    return line


def compute_obv_line(bars: list[PriceBar]) -> list[float]:
    if not bars:
        return []
    line = [0.0]
    for previous, current in zip(bars, bars[1:]):
        if current.close > previous.close:
            line.append(line[-1] + current.volume)
        elif current.close < previous.close:
            line.append(line[-1] - current.volume)
        else:
            line.append(line[-1])
    return [round(item, 4) for item in line]


def compute_cmf(bars: list[PriceBar], window: int = 20) -> float:
    subset = bars[-min(len(bars), window) :]
    if not subset:
        return 0.0
    money_flow_volume = 0.0
    total_volume = 0.0
    for bar in subset:
        if math.isclose(bar.high, bar.low):
            multiplier = 0.0
        else:
            multiplier = ((bar.close - bar.low) - (bar.high - bar.close)) / (bar.high - bar.low)
        money_flow_volume += multiplier * bar.volume
        total_volume += bar.volume
    if math.isclose(total_volume, 0.0):
        return 0.0
    return round(money_flow_volume / total_volume, 4)


def compute_volume_ratio(bars: list[PriceBar], window: int = 20) -> float:
    if not bars:
        return 0.0
    previous = bars[:-1][-min(max(len(bars) - 1, 0), window) :]
    if not previous:
        return 1.0
    average_volume = mean([bar.volume for bar in previous])
    if math.isclose(average_volume, 0.0):
        return 0.0
    return round(bars[-1].volume / average_volume, 4)


def percentile_rank(values: list[float], current: float) -> float:
    if not values:
        return 50.0
    count = sum(1 for value in values if value <= current)
    return round((count / len(values)) * 100, 2)


def load_asset_research(path: Path) -> dict[str, dict[str, Any]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return {str(item["asset_code"]): dict(item) for item in payload["assets"]}


def build_position_change_summary(
    current_state: PortfolioState, previous_state: PortfolioState
) -> list[dict[str, Any]]:
    previous_by_code = {asset.theme or asset.name: asset for asset in previous_state.assets}
    results: list[dict[str, Any]] = []
    for asset in current_state.assets:
        asset_code = asset.theme or asset.name
        previous = previous_by_code.get(asset_code)
        previous_value = previous.value if previous is not None else 0.0
        previous_shares = previous.shares if previous is not None and previous.shares is not None else 0.0
        current_shares = asset.shares if asset.shares is not None else 0.0
        amount_change = round(asset.value - previous_value, 2)
        share_change = round(current_shares - previous_shares, 4)
        last_price = round(asset.value / current_shares, 4) if current_shares else None
        previous_price = (
            round(previous.value / previous_shares, 4)
            if previous is not None and previous_shares
            else last_price
        )
        price_effect = (
            round(previous_shares * ((last_price or 0.0) - (previous_price or 0.0)), 2)
            if last_price is not None and previous_price is not None
            else 0.0
        )
        flow_effect = round(amount_change - price_effect, 2)
        total_cost_basis = (
            round((asset.average_cost or 0.0) * current_shares, 2)
            if asset.average_cost is not None and asset.shares is not None
            else None
        )
        results.append(
            {
                "asset_code": asset_code,
                "asset_name": asset.name,
                "category": asset.category,
                "asset_type": asset.asset_type or asset.category,
                "current_amount": round(asset.value, 2),
                "previous_amount": round(previous_value, 2),
                "amount_change": amount_change,
                "current_shares": round(current_shares, 4) if asset.shares is not None else None,
                "previous_shares": round(previous_shares, 4) if previous is not None else None,
                "share_change": share_change if asset.shares is not None else None,
                "average_cost": round(asset.average_cost, 4) if asset.average_cost is not None else None,
                "total_cost_basis": total_cost_basis,
                "price_effect": price_effect,
                "flow_effect": flow_effect,
                "estimated_unit_price": last_price,
            }
        )
    return results


def _level_to_severity(level: str) -> str:
    return {"observe": "low", "watch": "medium", "warning": "high"}[level]


def _build_signal(
    signal_name: str,
    level: str,
    asset_code: str,
    asset_name: str,
    message: str,
    evidence: dict[str, Any],
) -> dict[str, Any]:
    return {
        "signal_name": signal_name,
        "signal_type": signal_name,
        "level": level,
        "severity": _level_to_severity(level),
        "asset_code": asset_code,
        "asset_name": asset_name,
        "message": message,
        "evidence": evidence,
    }


def assess_asset_signals(
    asset: Asset, research: dict[str, Any], lookback_window: int = 20
) -> list[dict[str, Any]]:
    asset_code = asset.theme or asset.name
    bars = [PriceBar.from_dict(item) for item in research.get("recent_bars", [])]
    closes = [bar.close for bar in bars]
    signals: list[dict[str, Any]] = []

    if bars:
        ad_line = compute_ad_line(bars)
        obv_line = compute_obv_line(bars)
        cmf_20 = compute_cmf(bars, window=lookback_window)
        volume_ratio = compute_volume_ratio(bars, window=lookback_window)
        drawdown_20 = compute_drawdown_pct(closes, window=min(20, len(closes)))
        sma_20 = sma(closes, window=min(20, len(closes)))
        sma_60 = sma(closes, window=min(60, len(closes)))
        close_now = closes[-1]
        recent_high = max(closes[-min(lookback_window, len(closes)) :])

        distribution_conditions = [
            close_now >= recent_high * 0.97,
            len(ad_line) >= 2 and ad_line[-1] < max(ad_line[:-1]),
            len(obv_line) >= 2 and obv_line[-1] < max(obv_line[:-1]),
            cmf_20 < 0,
            len(closes) >= 3 and closes[-1] < max(closes[-3:]),
            volume_ratio >= 1.5 and len(closes) >= 2 and closes[-1] < closes[-2],
        ]
        distribution_score = sum(distribution_conditions)
        if distribution_score >= 3:
            level = "observe" if distribution_score == 3 else "watch" if distribution_score == 4 else "warning"
            signals.append(
                _build_signal(
                    "suspected_distribution",
                    level,
                    asset_code,
                    asset.name,
                    f"{asset.name} shows weakening volume-flow confirmation near recent highs",
                    {
                        "distribution_score": distribution_score,
                        "cmf_20": cmf_20,
                        "volume_ratio_20": volume_ratio,
                        "drawdown_20_pct": drawdown_20,
                    },
                )
            )

        shakeout = (
            close_now > sma_60
            and -12.0 <= drawdown_20 <= -5.0
            and volume_ratio >= 1.5
            and close_now >= sma_20
        )
        if shakeout:
            signals.append(
                _build_signal(
                    "possible_shakeout",
                    "watch",
                    asset_code,
                    asset.name,
                    f"{asset.name} pulled back sharply but retained its medium-term trend",
                    {
                        "drawdown_20_pct": drawdown_20,
                        "sma_20": round(sma_20, 4),
                        "sma_60": round(sma_60, 4),
                        "volume_ratio_20": volume_ratio,
                    },
                )
            )

        trend_break = close_now < sma_60 and sma_20 < sma_60 and cmf_20 < 0 and drawdown_20 <= -10.0
        if trend_break:
            signals.append(
                _build_signal(
                    "trend_break_warning",
                    "warning",
                    asset_code,
                    asset.name,
                    f"{asset.name} fell below its medium-term trend with weak money flow",
                    {
                        "drawdown_20_pct": drawdown_20,
                        "sma_20": round(sma_20, 4),
                        "sma_60": round(sma_60, 4),
                        "cmf_20": cmf_20,
                    },
                )
            )

    fair_value = research.get("fair_value")
    current_price = research.get("current_price")
    if fair_value is not None and current_price is not None and float(fair_value) > 0:
        price_fair_value = round(float(current_price) / float(fair_value), 4)
        if price_fair_value > 1.1:
            level = "observe" if price_fair_value <= 1.2 else "watch" if price_fair_value <= 1.3 else "warning"
            signals.append(
                _build_signal(
                    "valuation_premium_warning",
                    level,
                    asset_code,
                    asset.name,
                    f"{asset.name} is trading at a premium to its fair-value estimate",
                    {"price_fair_value": price_fair_value, "fair_value": fair_value, "current_price": current_price},
                )
            )
        elif price_fair_value < 0.9:
            level = "observe" if price_fair_value >= 0.8 else "watch" if price_fair_value >= 0.7 else "warning"
            signals.append(
                _build_signal(
                    "valuation_discount_watch",
                    level,
                    asset_code,
                    asset.name,
                    f"{asset.name} is trading below its fair-value estimate",
                    {"price_fair_value": price_fair_value, "fair_value": fair_value, "current_price": current_price},
                )
            )

    sharpe_ratio = research.get("sharpe_ratio")
    category_sharpe = research.get("category_sharpe")
    max_drawdown = research.get("max_drawdown")
    category_max_drawdown = research.get("category_max_drawdown")
    volatility = research.get("volatility")
    category_volatility = research.get("category_volatility")
    deterioration_conditions = 0
    if sharpe_ratio is not None and category_sharpe not in (None, 0):
        if float(sharpe_ratio) < float(category_sharpe) * 0.8:
            deterioration_conditions += 1
    if max_drawdown is not None and category_max_drawdown not in (None, 0):
        if abs(float(max_drawdown)) > abs(float(category_max_drawdown)) * 1.2:
            deterioration_conditions += 1
    if volatility is not None and category_volatility not in (None, 0):
        if float(volatility) > float(category_volatility) * 1.2:
            deterioration_conditions += 1
    if deterioration_conditions >= 2:
        signals.append(
            _build_signal(
                "risk_adjusted_return_deterioration",
                "watch" if deterioration_conditions == 2 else "warning",
                asset_code,
                asset.name,
                f"{asset.name} is lagging its category on risk-adjusted metrics",
                {
                    "sharpe_ratio": sharpe_ratio,
                    "category_sharpe": category_sharpe,
                    "max_drawdown": max_drawdown,
                    "category_max_drawdown": category_max_drawdown,
                    "volatility": volatility,
                    "category_volatility": category_volatility,
                },
            )
        )

    if research.get("manager_changed") or research.get("style_drift"):
        signals.append(
            _build_signal(
                "manager_style_drift",
                "watch",
                asset_code,
                asset.name,
                f"{asset.name} shows manager or style drift risk",
                {
                    "manager_changed": bool(research.get("manager_changed")),
                    "style_drift": bool(research.get("style_drift")),
                    "fund_manager": research.get("fund_manager"),
                },
            )
        )

    return signals


def build_asset_signal_review(
    current_state: PortfolioState,
    previous_state: PortfolioState,
    research_by_code: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    positions = build_position_change_summary(current_state, previous_state)
    total_value = current_state.total_value or 1.0
    research_highlights: list[dict[str, Any]] = []
    signals: list[dict[str, Any]] = []
    for asset in current_state.assets:
        asset_code = asset.theme or asset.name
        weight_pct = round((asset.value / total_value) * 100, 4)
        research = research_by_code.get(asset_code, {})
        if research:
            highlight = {
                "asset_code": asset_code,
                "asset_name": asset.name,
                "weight_pct": weight_pct,
                "sector": research.get("sector"),
                "companies": research.get("companies", []),
                "fund_manager": research.get("fund_manager"),
                "hot_topics": research.get("hot_topics", []),
                "fair_value": research.get("fair_value"),
                "current_price": research.get("current_price"),
                "sharpe_ratio": research.get("sharpe_ratio"),
                "max_drawdown": research.get("max_drawdown"),
            }
            research_highlights.append(highlight)
            signals.extend(assess_asset_signals(asset, research))
    positions.sort(key=lambda item: item["current_amount"], reverse=True)
    research_highlights.sort(key=lambda item: item["weight_pct"], reverse=True)
    severity_rank = {"high": 3, "medium": 2, "low": 1}
    signals.sort(key=lambda item: (severity_rank[item["severity"]], item["asset_code"]), reverse=True)
    return {
        "positions": positions,
        "research_highlights": research_highlights,
        "signals": signals,
    }
