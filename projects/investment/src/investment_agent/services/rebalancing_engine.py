from __future__ import annotations


def evaluate_rebalance(
    allocations_pct: dict[str, float],
    targets: dict[str, float],
    threshold_pct: float = 10.0,
) -> dict[str, object]:
    breaches: list[dict[str, object]] = []
    for category, target_fraction in targets.items():
        target_pct = target_fraction * 100
        current_pct = allocations_pct.get(category, 0.0)
        lower = round(target_pct - threshold_pct, 4)
        upper = round(target_pct + threshold_pct, 4)
        if current_pct < lower or current_pct > upper:
            direction = "overweight" if current_pct > upper else "underweight"
            breaches.append(
                {
                    "category": category,
                    "target_pct": round(target_pct, 4),
                    "current_pct": round(current_pct, 4),
                    "lower_bound_pct": lower,
                    "upper_bound_pct": upper,
                    "direction": direction,
                }
            )

    triggered = bool(breaches)
    reasons = [
        f"{item['category']} exceeded {'upper' if item['direction'] == 'overweight' else 'lower'} bound"
        for item in breaches
    ]
    return {
        "triggered": triggered,
        "threshold_pct": threshold_pct,
        "breaches": breaches,
        "reasons": reasons,
        "priority_action": (
            "use new funds to repair underweight allocations before considering sells"
            if triggered
            else "continue observation"
        ),
    }
