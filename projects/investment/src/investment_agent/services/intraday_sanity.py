from __future__ import annotations

from typing import Any

from investment_agent.services.intraday_proxy_engine import classify_intraday_sentiment


def run_intraday_sentiment_sanity(thresholds: dict[str, Any] | None = None) -> dict[str, str]:
    scenarios = {
        "panic": {
            "price_trend_pct": -2.4,
            "volume_ratio": 1.9,
            "amplitude_pct": 4.3,
            "drawdown_from_high_pct": -2.2,
        },
        "washout": {
            "price_trend_pct": -0.6,
            "volume_ratio": 1.42,
            "amplitude_pct": 3.8,
            "drawdown_from_high_pct": -2.2,
        },
        "chase": {
            "price_trend_pct": 1.5,
            "volume_ratio": 1.4,
            "amplitude_pct": 1.8,
            "drawdown_from_high_pct": -0.4,
        },
        "chop": {
            "price_trend_pct": 0.3,
            "volume_ratio": 0.98,
            "amplitude_pct": 1.2,
            "drawdown_from_high_pct": -0.5,
        },
        "drift_down": {
            "price_trend_pct": -0.9,
            "volume_ratio": 0.82,
            "amplitude_pct": 1.4,
            "drawdown_from_high_pct": -1.1,
        },
        "rebound": {
            "price_trend_pct": 0.8,
            "volume_ratio": 0.9,
            "amplitude_pct": 1.6,
            "drawdown_from_high_pct": -0.3,
        },
        "breakout": {
            "price_trend_pct": 2.2,
            "volume_ratio": 1.75,
            "amplitude_pct": 2.4,
            "drawdown_from_high_pct": -0.2,
        },
        "stall": {
            "price_trend_pct": 1.1,
            "volume_ratio": 1.05,
            "amplitude_pct": 1.6,
            "drawdown_from_high_pct": -1.0,
        },
    }
    return {name: classify_intraday_sentiment(metrics, thresholds)["label"] for name, metrics in scenarios.items()}
