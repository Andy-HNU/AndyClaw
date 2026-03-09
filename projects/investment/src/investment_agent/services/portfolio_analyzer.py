from __future__ import annotations

import json
from pathlib import Path

from investment_agent.models.portfolio import Asset, PortfolioState


def load_portfolio_state(path: Path) -> PortfolioState:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    assets = [Asset.from_dict(item) for item in payload["assets"]]
    return PortfolioState(updated_at=str(payload["updated_at"]), assets=assets)


def load_target_allocation(path: Path) -> dict[str, float]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return {str(key): float(value) for key, value in payload.items()}


def calculate_allocations(state: PortfolioState) -> dict[str, float]:
    total = state.total_value
    if total <= 0:
        return {category: 0.0 for category in state.grouped_values()}
    return {
        category: round((value / total) * 100, 4)
        for category, value in state.grouped_values().items()
    }


def calculate_deviations(
    allocations_pct: dict[str, float], targets: dict[str, float]
) -> dict[str, float]:
    deviations: dict[str, float] = {}
    for category, target_fraction in targets.items():
        target_pct = target_fraction * 100
        deviations[category] = round(allocations_pct.get(category, 0.0) - target_pct, 4)
    return deviations


def build_portfolio_analysis(portfolio_state_path: Path, target_allocation_path: Path) -> dict[str, object]:
    state = load_portfolio_state(portfolio_state_path)
    targets = load_target_allocation(target_allocation_path)
    allocations = calculate_allocations(state)
    deviations = calculate_deviations(allocations, targets)
    return {
        "updated_at": state.updated_at,
        "total_value": round(state.total_value, 2),
        "grouped_values": {key: round(value, 2) for key, value in state.grouped_values().items()},
        "targets_pct": {key: round(value * 100, 4) for key, value in targets.items()},
        "allocations_pct": allocations,
        "deviations_pct": deviations,
    }
