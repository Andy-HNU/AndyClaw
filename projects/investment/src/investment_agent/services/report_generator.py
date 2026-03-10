from __future__ import annotations


def generate_monthly_report(
    analysis: dict[str, object],
    rebalance_result: dict[str, object],
    monthly_plan: dict[str, object],
    risk_signals: list[dict[str, object]],
    news_items: list[dict[str, object]],
    position_changes: list[dict[str, object]],
    research_highlights: list[dict[str, object]],
) -> dict[str, object]:
    title = f"{analysis['updated_at']} 投资月报"
    observation_points = [item["title"] for item in news_items[:3]]
    content_json = {
        "portfolio": {
            "total_value": analysis["total_value"],
            "allocations_pct": analysis["allocations_pct"],
            "deviations_pct": analysis["deviations_pct"],
        },
        "position_changes": position_changes,
        "research_highlights": research_highlights,
        "rebalance": rebalance_result,
        "monthly_plan": monthly_plan,
        "risk_summary": risk_signals,
        "news_observations": news_items,
        "next_month_watchlist": observation_points,
    }
    position_lines = [
        (
            f"- {item['asset_name']}: 金额 {item['current_amount']:.2f}, "
            f"金额变化 {item['amount_change']:.2f}, "
            f"份额变化 {float(item['share_change']):.4f}"
        )
        for item in position_changes[:5]
        if item["share_change"] is not None
    ] or ["- 暂无细化仓位变化摘要"]
    research_lines = [
        (
            f"- {item['asset_name']}: 板块 {item['sector'] or '未标注'}, "
            f"基金经理 {item['fund_manager'] or '未标注'}, "
            f"热点 {', '.join(item['hot_topics']) if item['hot_topics'] else '暂无'}"
        )
        for item in research_highlights[:5]
    ] or ["- 暂无资产研究摘要"]

    plan_lines = [
        f"- {item['category']}: {item['recommended_amount']:.2f} ({item['reason']})"
        for item in monthly_plan["recommendations"]
    ] or ["- 当前偏离可接受，新增资金保持灵活"]
    risk_lines = [
        f"- {item['signal_type']}: {item['message']}"
        for item in risk_signals
    ] or ["- 暂无新增风险信号"]
    news_lines = [
        f"- [{item['topic']}] {item['title']} ({item['sentiment_hint']})"
        for item in news_items
    ] or ["- 暂无新闻摘要"]
    watchlist_lines = [f"- {item}" for item in observation_points] or [
        "- 继续跟踪仓位偏离与核心资产估值"
    ]

    content_md = "\n".join(
        [
            f"# {title}",
            "",
            "## 月末仓位与偏离",
            f"- 总资产: {analysis['total_value']:.2f}",
            f"- 当前比例: {analysis['allocations_pct']}",
            f"- 相对目标偏离: {analysis['deviations_pct']}",
            "",
            "## 细分持仓变化",
            *position_lines,
            "",
            "## 再平衡检查",
            f"- 是否触发: {'是' if rebalance_result['triggered'] else '否'}",
            f"- 优先动作: {rebalance_result['priority_action']}",
            "",
            "## 下月定投建议",
            *plan_lines,
            "",
            "## 风险摘要",
            *risk_lines,
            "",
            "## 资产研究摘要",
            *research_lines,
            "",
            "## 新闻与行业观察",
            *news_lines,
            "",
            "## 下月观察点",
            *watchlist_lines,
        ]
    )
    return {
        "report_type": "monthly",
        "title": title,
        "content_md": content_md,
        "content_json": content_json,
    }
