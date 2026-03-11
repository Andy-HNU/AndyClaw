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
            "price_trend_pct": -1.0,
            "volume_ratio": 1.45,
            "amplitude_pct": 3.6,
            "drawdown_from_high_pct": -1.4,
        },
        "chase": {
            "price_trend_pct": 1.6,
            "volume_ratio": 1.42,
            "amplitude_pct": 2.2,
            "drawdown_from_high_pct": -0.6,
        },
        "chop": {
            "price_trend_pct": 0.2,
            "volume_ratio": 0.95,
            "amplitude_pct": 1.1,
            "drawdown_from_high_pct": -0.4,
        },
    }
    return {name: classify_intraday_sentiment(metrics, thresholds)["label"] for name, metrics in scenarios.items()}
