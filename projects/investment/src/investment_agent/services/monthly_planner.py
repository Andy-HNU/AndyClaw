from __future__ import annotations


def build_monthly_plan(
    analysis: dict[str, object],
    targets: dict[str, float],
    monthly_budget: float = 12000.0,
) -> dict[str, object]:
    total_value = float(analysis["total_value"])
    allocations_pct = {
        str(key): float(value) for key, value in dict(analysis["allocations_pct"]).items()
    }
    deficits: dict[str, float] = {}
    for category, target_fraction in targets.items():
        target_value = total_value * float(target_fraction)
        current_value = total_value * allocations_pct.get(category, 0.0) / 100.0
        gap_value = round(target_value - current_value, 2)
        if gap_value > 0:
            deficits[category] = gap_value

    total_gap = round(sum(deficits.values()), 2)
    recommendations: list[dict[str, object]] = []
    remaining_budget = round(monthly_budget, 2)
    for category, gap_value in sorted(deficits.items(), key=lambda item: item[1], reverse=True):
        if total_gap <= 0:
            recommended = 0.0
        else:
            recommended = round(monthly_budget * gap_value / total_gap, 2)
        if recommended > remaining_budget:
            recommended = remaining_budget
        remaining_budget = round(remaining_budget - recommended, 2)
        recommendations.append(
            {
                "category": category,
                "gap_value": gap_value,
                "recommended_amount": recommended,
                "reason": f"{category} is under target and should receive new funds first",
            }
        )

    if recommendations and remaining_budget != 0:
        recommendations[0]["recommended_amount"] = round(
            float(recommendations[0]["recommended_amount"]) + remaining_budget, 2
        )
        remaining_budget = 0.0

    status = "needs_repair" if recommendations else "balanced"
    return {
        "monthly_budget": round(monthly_budget, 2),
        "status": status,
        "underweight_categories": [item["category"] for item in recommendations],
        "recommendations": recommendations,
        "remaining_budget": remaining_budget,
        "rationale": (
            "allocate new capital to underweight sleeves before adding to overweight assets"
            if recommendations
            else "current allocation is close enough to target; keep new funding flexible"
        ),
    }
