from __future__ import annotations

from investment_agent.config import ProjectPaths
from investment_agent.db.repository import InvestmentRepository
from investment_agent.providers import (
    MarketQuote,
    NewsItem,
    build_default_intraday_data_chain,
    build_default_market_data_chain,
    build_default_news_data_chain,
    refresh_intraday_proxy_inputs,
    refresh_market_quotes,
    refresh_news_items,
)
from investment_agent.services.portfolio_analyzer import (
    build_portfolio_analysis,
    load_portfolio_state,
    load_target_allocation,
)
from investment_agent.services.chart_artifacts import render_daily_price_chart
from investment_agent.services.intraday_proxy_engine import build_intraday_proxy_review
from investment_agent.services.rebalancing_engine import evaluate_rebalance
from investment_agent.services.report_generator import generate_daily_report
from investment_agent.services.signal_engine import build_asset_signal_review, load_asset_research


def _derive_data_quality(price_refresh: dict[str, object], news_refresh: dict[str, object]) -> tuple[str, dict[str, object]]:
    sources = {
        "market": {
            "status": price_refresh.get("status"),
            "source": price_refresh.get("source"),
            "used_backup": bool(price_refresh.get("used_backup", False)),
            "errors": list(price_refresh.get("errors", [])),
        },
        "news": {
            "status": news_refresh.get("status"),
            "source": news_refresh.get("source"),
            "used_backup": bool(news_refresh.get("used_backup", False)),
            "errors": list(news_refresh.get("errors", [])),
        },
    }
    statuses = {
        "market": "fallback" if sources["market"]["used_backup"] else ("real" if sources["market"]["status"] == "success" else "fallback"),
        "news": "fallback" if sources["news"]["used_backup"] else ("real" if sources["news"]["status"] == "success" else "fallback"),
    }
    if statuses["market"] == "real" and statuses["news"] == "real":
        quality = "real"
    elif statuses["market"] == "fallback" and statuses["news"] == "fallback":
        quality = "fallback"
    else:
        quality = "mixed"
    return quality, sources


def run_daily_review(
    paths: ProjectPaths,
    repository: InvestmentRepository,
    news_limit: int = 5,
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
    targets = load_target_allocation(paths.target_allocation_path)
    rebalance_result = evaluate_rebalance(analysis["allocations_pct"], targets)
    signal_review = build_asset_signal_review(portfolio_state, previous_portfolio_state, research_by_code)
    intraday_primary, *intraday_rest = build_default_intraday_data_chain(paths)
    intraday_refresh = refresh_intraday_proxy_inputs(
        intraday_primary,
        intraday_rest[0] if intraday_rest else None,
    )
    intraday_market = build_intraday_proxy_review(
        portfolio_state=portfolio_state,
        config_path=paths.intraday_proxy_config_path,
        realtime_path=paths.intraday_realtime_path,
        realtime_payload=intraday_refresh,
    )
    chart_candidates = sorted(
        [asset for asset in portfolio_state.assets if asset.category != "cash"],
        key=lambda asset: asset.value,
        reverse=True,
    )[:2]
    chart_series: list[dict[str, object]] = []
    for asset in chart_candidates:
        asset_code = asset.theme or asset.name
        history = repository.fetch_recent_price_history(asset_code, limit=30)
        points = [
            {
                "x": str(item["trade_date"])[5:] if len(str(item["trade_date"])) >= 10 else str(item["trade_date"]),
                "y": float(item["close_price"]),
            }
            for item in history
            if item.get("close_price") is not None
        ]
        if points:
            chart_series.append(
                {
                    "name": f"{asset.name}({asset.symbol})" if asset.symbol else asset.name,
                    "points": points,
                }
            )
    chart_result = render_daily_price_chart(
        paths=paths,
        series=chart_series,
        report_time=str(analysis["updated_at"]),
    )
    data_quality, provider_notes = _derive_data_quality(price_refresh, news_refresh)
    report = generate_daily_report(
        analysis=analysis,
        rebalance_result=rebalance_result,
        risk_signals=list(signal_review["signals"]),
        news_items=news_items,
        chart_artifacts=[chart_result],
        intraday_market=intraday_market,
        data_quality=data_quality,
        provider_notes=provider_notes,
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
        "intraday_refresh": intraday_refresh,
        "rebalance": rebalance_result,
        "signal_review": signal_review,
        "intraday_market": intraday_market,
        "chart_artifacts": [chart_result],
        "report_id": report_id,
        "report": report,
    }
