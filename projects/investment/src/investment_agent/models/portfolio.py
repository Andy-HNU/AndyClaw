from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Asset:
    name: str
    category: str
    value: float
    theme: str | None = None
    profit: float | None = None
    shares: float | None = None
    average_cost: float | None = None
    asset_type: str | None = None
    symbol: str | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Asset":
        return cls(
            name=str(payload["name"]),
            category=str(payload["category"]),
            value=float(payload["value"]),
            theme=payload.get("theme"),
            profit=float(payload["profit"]) if payload.get("profit") is not None else None,
            shares=float(payload["shares"]) if payload.get("shares") is not None else None,
            average_cost=(
                float(payload["average_cost"]) if payload.get("average_cost") is not None else None
            ),
            asset_type=str(payload["asset_type"]) if payload.get("asset_type") is not None else None,
            symbol=str(payload["symbol"]) if payload.get("symbol") is not None else None,
        )


@dataclass(frozen=True)
class PortfolioState:
    updated_at: str
    assets: list[Asset]

    @property
    def total_value(self) -> float:
        return sum(asset.value for asset in self.assets)

    def grouped_values(self) -> dict[str, float]:
        grouped: dict[str, float] = {}
        for asset in self.assets:
            grouped[asset.category] = grouped.get(asset.category, 0.0) + asset.value
        return grouped
