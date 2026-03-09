from __future__ import annotations

from investment_agent.db.repository import InvestmentRepository


def persist_rebalance_review(
    repository: InvestmentRepository,
    analysis: dict[str, object],
    rebalance_result: dict[str, object],
) -> dict[str, object]:
    suggestion_id = repository.store_investment_suggestion(
        suggestion_time=str(analysis["updated_at"]),
        suggestion_type="rebalance_review",
        content={
            "analysis_summary": {
                "total_value": analysis["total_value"],
                "allocations_pct": analysis["allocations_pct"],
                "deviations_pct": analysis["deviations_pct"],
            },
            "rebalance_result": rebalance_result,
        },
        rationale=str(rebalance_result["priority_action"]),
        status="ready" if rebalance_result["triggered"] else "observation",
    )

    risk_signal_ids: list[int] = []
    for breach in rebalance_result["breaches"]:
        severity = "high" if abs(float(breach["current_pct"]) - float(breach["target_pct"])) >= 15 else "medium"
        signal_id = repository.store_risk_signal(
            signal_time=str(analysis["updated_at"]),
            signal_type="allocation_drift",
            severity=severity,
            message=(
                f"{breach['category']} is {breach['direction']} "
                f"({breach['current_pct']}% vs target {breach['target_pct']}%)"
            ),
            evidence={
                "breach": breach,
                "priority_action": rebalance_result["priority_action"],
            },
            status="open",
        )
        risk_signal_ids.append(signal_id)

    return {
        "suggestion_id": suggestion_id,
        "risk_signal_ids": risk_signal_ids,
        "latest_suggestion": repository.fetch_latest_investment_suggestion(),
        "open_risk_signals": repository.fetch_open_risk_signals(),
    }
