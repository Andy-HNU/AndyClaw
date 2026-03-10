from __future__ import annotations

from investment_agent.config import ProjectPaths
from investment_agent.db.repository import InvestmentRepository
from investment_agent.providers import (
    MarketQuote,
    NewsItem,
    build_default_market_data_chain,
    build_default_news_data_chain,
    refresh_market_quotes,
    refresh_news_items,
)
from investment_agent.services.monthly_planner import build_monthly_plan
from investment_agent.services.portfolio_analyzer import (
    build_portfolio_analysis,
    load_portfolio_state,
    load_target_allocation,
)
from investment_agent.services.rebalance_recorder import persist_rebalance_review
from investment_agent.services.rebalancing_engine import evaluate_rebalance
from investment_agent.services.report_generator import generate_monthly_report
from investment_agent.services.signal_engine import build_asset_signal_review, load_asset_research


def run_monthly_review(
    paths: ProjectPaths,
    repository: InvestmentRepository,
    news_limit: int = 5,
    monthly_budget: float = 12000.0,
) -> dict[str, object]:
    repository.initialize()
    portfolio_state = load_portfolio_state(paths.portfolio_state_path)
    previous_portfolio_state = load_portfolio_state(paths.previous_portfolio_state_path)
    research_by_code = load_asset_research(paths.asset_research_path)
    asset_codes = [asset.theme or asset.name for asset in portfolio_state.assets]

    primary_market, backup_market = build_default_market_data_chain(paths)
    price_refresh = refresh_market_quotes(asset_codes, primary_market, backup_market)
    if price_refresh["status"] == "success":
        quotes = [
            MarketQuote.from_dict(item, default_source=str(price_refresh["source"]))
            for item in price_refresh["quotes"]
        ]
        repository.store_price_snapshots(quotes)

    primary_news, backup_news = build_default_news_data_chain(paths)
    news_refresh = refresh_news_items(primary_news, backup_news, limit=news_limit)
    news_items: list[dict[str, object]] = []
    if news_refresh["status"] == "success":
        news = [
            NewsItem.from_dict(item, default_source=str(news_refresh["source"]))
            for item in news_refresh["news"]
        ]
        repository.store_news_items(news)
        news_items = [item.to_dict() for item in news]

    analysis = build_portfolio_analysis(paths.portfolio_state_path, paths.target_allocation_path)
    analysis_result_id = repository.store_analysis_result(analysis)
    targets = load_target_allocation(paths.target_allocation_path)
    rebalance_result = evaluate_rebalance(analysis["allocations_pct"], targets)
    persisted_rebalance = persist_rebalance_review(repository, analysis, rebalance_result)
    monthly_plan = build_monthly_plan(analysis, targets, monthly_budget=monthly_budget)
    signal_review = build_asset_signal_review(portfolio_state, previous_portfolio_state, research_by_code)
    v2_signal_ids: list[int] = []
    for signal in signal_review["signals"]:
        v2_signal_ids.append(
            repository.store_risk_signal(
                signal_time=str(analysis["updated_at"]),
                signal_type=str(signal["signal_type"]),
                severity=str(signal["severity"]),
                message=str(signal["message"]),
                evidence=dict(signal["evidence"]),
                status="open",
            )
        )
    risk_signals = list(persisted_rebalance["risk_signals"]) + repository.fetch_risk_signals_by_ids(v2_signal_ids)
    report = generate_monthly_report(
        analysis=analysis,
        rebalance_result=rebalance_result,
        monthly_plan=monthly_plan,
        risk_signals=risk_signals,
        news_items=news_items,
        position_changes=list(signal_review["positions"]),
        research_highlights=list(signal_review["research_highlights"]),
    )
    report_id = repository.store_report(
        report_time=str(analysis["updated_at"]),
        report_type=str(report["report_type"]),
        title=str(report["title"]),
        content_md=str(report["content_md"]),
        content_json=dict(report["content_json"]),
    )
    return {
        "status": "success",
        "price_refresh": price_refresh,
        "news_refresh": news_refresh,
        "analysis_result_id": analysis_result_id,
        "rebalance": rebalance_result,
        "persisted_rebalance": persisted_rebalance,
        "signal_review": signal_review,
        "monthly_plan": monthly_plan,
        "report_id": report_id,
        "report": report,
    }
