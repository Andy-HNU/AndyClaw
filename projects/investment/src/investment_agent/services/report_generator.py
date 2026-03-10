from __future__ import annotations


def _build_summary(
    report_type: str,
    total_value: float,
    risk_signals: list[dict[str, object]],
    news_items: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "report_type": report_type,
        "total_value": round(total_value, 2),
        "risk_signal_count": len(risk_signals),
        "news_count": len(news_items),
    }


def generate_daily_report(
    analysis: dict[str, object],
    rebalance_result: dict[str, object],
    risk_signals: list[dict[str, object]],
    news_items: list[dict[str, object]],
) -> dict[str, object]:
    title = f"{analysis['updated_at']} 投资日报"
    action_items = []
    if rebalance_result["triggered"]:
        action_items.append(rebalance_result["priority_action"])
    action_items.extend([item["title"] for item in news_items[:3]])
    sections = [
        {
            "section_id": "portfolio_snapshot",
            "title": "今日仓位快照",
            "items": [
                {"label": "total_value", "value": analysis["total_value"]},
                {"label": "allocations_pct", "value": analysis["allocations_pct"]},
                {"label": "deviations_pct", "value": analysis["deviations_pct"]},
            ],
        },
        {"section_id": "rebalance_review", "title": "再平衡检查", "items": [rebalance_result]},
        {"section_id": "risk_summary", "title": "今日风险摘要", "items": risk_signals},
        {"section_id": "news_summary", "title": "今日板块新闻", "items": news_items},
        {"section_id": "action_items", "title": "建议动作", "items": action_items},
    ]
    risk_lines = [f"- {item['signal_type']}: {item['message']}" for item in risk_signals[:5]] or ["- 暂无新增风险"]
    news_lines = [f"- [{item['topic']}] {item['title']}" for item in news_items[:5]] or ["- 暂无新闻摘要"]
    action_lines = [f"- {item}" for item in action_items] or ["- 保持观察，等待更多证据"]
    content_md = "\n".join(
        [
            f"# {title}",
            "",
            "## 今日仓位快照",
            f"- 总资产: {analysis['total_value']:.2f}",
            f"- 当前比例: {analysis['allocations_pct']}",
            f"- 相对目标偏离: {analysis['deviations_pct']}",
            "",
            "## 再平衡检查",
            f"- 是否触发: {'是' if rebalance_result['triggered'] else '否'}",
            f"- 优先动作: {rebalance_result['priority_action']}",
            "",
            "## 今日风险摘要",
            *risk_lines,
            "",
            "## 今日板块新闻",
            *news_lines,
            "",
            "## 建议动作",
            *action_lines,
        ]
    )
    content_json = {
        "schema_version": "1.0",
        "report_type": "daily",
        "report_time": analysis["updated_at"],
        "title": title,
        "summary": _build_summary(
            report_type="daily",
            total_value=float(analysis["total_value"]),
            risk_signals=risk_signals,
            news_items=news_items,
        ),
        "sections": sections,
        "portfolio": {
            "total_value": analysis["total_value"],
            "allocations_pct": analysis["allocations_pct"],
            "deviations_pct": analysis["deviations_pct"],
        },
        "rebalance": rebalance_result,
        "risk_summary": risk_signals,
        "news_observations": news_items,
        "action_items": action_items,
    }
    return {
        "report_type": "daily",
        "title": title,
        "content_md": content_md,
        "content_json": content_json,
    }


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
    sections = [
        {
            "section_id": "portfolio_snapshot",
            "title": "月末仓位与偏离",
            "items": [
                {"label": "total_value", "value": analysis["total_value"]},
                {"label": "allocations_pct", "value": analysis["allocations_pct"]},
                {"label": "deviations_pct", "value": analysis["deviations_pct"]},
            ],
        },
        {"section_id": "position_changes", "title": "细分持仓变化", "items": position_changes},
        {"section_id": "rebalance_review", "title": "再平衡检查", "items": [rebalance_result]},
        {"section_id": "monthly_plan", "title": "下月定投建议", "items": monthly_plan["recommendations"]},
        {"section_id": "risk_summary", "title": "风险摘要", "items": risk_signals},
        {"section_id": "research_highlights", "title": "资产研究摘要", "items": research_highlights},
        {"section_id": "news_summary", "title": "新闻与行业观察", "items": news_items},
        {"section_id": "watchlist", "title": "下月观察点", "items": observation_points},
    ]
    content_json = {
        "schema_version": "1.0",
        "report_type": "monthly",
        "report_time": analysis["updated_at"],
        "title": title,
        "summary": _build_summary(
            report_type="monthly",
            total_value=float(analysis["total_value"]),
            risk_signals=risk_signals,
            news_items=news_items,
        ),
        "sections": sections,
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


def generate_weekly_report(
    analysis: dict[str, object],
    position_changes: list[dict[str, object]],
    risk_signals: list[dict[str, object]],
    news_items: list[dict[str, object]],
) -> dict[str, object]:
    title = f"{analysis['updated_at']} 投资周报"
    watchlist = [item["title"] for item in news_items[:3]]
    sections = [
        {
            "section_id": "portfolio_snapshot",
            "title": "本周仓位快照",
            "items": [
                {"label": "total_value", "value": analysis["total_value"]},
                {"label": "allocations_pct", "value": analysis["allocations_pct"]},
            ],
        },
        {"section_id": "position_changes", "title": "本周持仓变化", "items": position_changes},
        {"section_id": "risk_summary", "title": "风险预警", "items": risk_signals},
        {"section_id": "news_summary", "title": "本周重要新闻", "items": news_items},
        {"section_id": "watchlist", "title": "待验证事项", "items": watchlist},
    ]
    position_lines = [
        f"- {item['asset_name']}: 金额变化 {item['amount_change']:.2f}, 份额变化 {float(item['share_change']):.4f}"
        for item in position_changes[:5]
        if item["share_change"] is not None
    ] or ["- 暂无本周持仓变化摘要"]
    risk_lines = [f"- {item['signal_name']}: {item['message']}" for item in risk_signals[:5]] or ["- 暂无新增风险"]
    news_lines = [f"- [{item['topic']}] {item['title']}" for item in news_items[:5]] or ["- 暂无新闻摘要"]
    watchlist_lines = [f"- {item}" for item in watchlist] or ["- 继续跟踪核心仓位与主题波动"]
    content_md = "\n".join(
        [
            f"# {title}",
            "",
            "## 本周仓位快照",
            f"- 总资产: {analysis['total_value']:.2f}",
            f"- 当前比例: {analysis['allocations_pct']}",
            "",
            "## 本周持仓变化",
            *position_lines,
            "",
            "## 风险预警",
            *risk_lines,
            "",
            "## 本周重要新闻",
            *news_lines,
            "",
            "## 待验证事项",
            *watchlist_lines,
        ]
    )
    content_json = {
        "schema_version": "1.0",
        "report_type": "weekly",
        "report_time": analysis["updated_at"],
        "title": title,
        "summary": _build_summary(
            report_type="weekly",
            total_value=float(analysis["total_value"]),
            risk_signals=risk_signals,
            news_items=news_items,
        ),
        "sections": sections,
        "portfolio": {
            "total_value": analysis["total_value"],
            "allocations_pct": analysis["allocations_pct"],
        },
        "position_changes": position_changes,
        "risk_summary": risk_signals,
        "news_observations": news_items,
        "watchlist": watchlist,
    }
    return {
        "report_type": "weekly",
        "title": title,
        "content_md": content_md,
        "content_json": content_json,
    }
