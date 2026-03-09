from __future__ import annotations

import argparse
import json

from investment_agent.config import discover_paths
from investment_agent.db.repository import InvestmentRepository
from investment_agent.providers import JsonFileMarketDataProvider, MarketQuote, refresh_market_quotes
from investment_agent.services.portfolio_analyzer import (
    build_portfolio_analysis,
    load_target_allocation,
    load_portfolio_state,
)
from investment_agent.services.rebalancing_engine import evaluate_rebalance


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Investment agent utilities")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init-db", help="Initialize SQLite and seed first snapshot")
    subparsers.add_parser("portfolio-summary", help="Print current portfolio summary")
    subparsers.add_parser("rebalance-check", help="Evaluate rebalance trigger")
    subparsers.add_parser("persist-analysis", help="Persist the current portfolio analysis")
    subparsers.add_parser("refresh-prices", help="Refresh latest price snapshots with fallback")
    return parser


def cmd_init_db() -> int:
    paths = discover_paths()
    repository = InvestmentRepository(paths.db_path, paths.schema_path)
    portfolio_state = load_portfolio_state(paths.portfolio_state_path)
    repository.initialize()
    repository.seed_portfolio_state(portfolio_state)
    latest = repository.fetch_latest_snapshot()
    print(
        json.dumps(
            {
                "db_path": str(paths.db_path),
                "seeded_assets": len(portfolio_state.assets),
                "latest_snapshot": latest,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def cmd_portfolio_summary() -> int:
    paths = discover_paths()
    analysis = build_portfolio_analysis(paths.portfolio_state_path, paths.target_allocation_path)
    print(json.dumps(analysis, ensure_ascii=False, indent=2))
    return 0


def cmd_rebalance_check() -> int:
    paths = discover_paths()
    analysis = build_portfolio_analysis(paths.portfolio_state_path, paths.target_allocation_path)
    targets = load_target_allocation(paths.target_allocation_path)
    result = evaluate_rebalance(analysis["allocations_pct"], targets)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_persist_analysis() -> int:
    paths = discover_paths()
    repository = InvestmentRepository(paths.db_path, paths.schema_path)
    repository.initialize()
    analysis = build_portfolio_analysis(paths.portfolio_state_path, paths.target_allocation_path)
    row_id = repository.store_analysis_result(analysis)
    latest = repository.fetch_latest_analysis()
    print(
        json.dumps(
            {
                "db_path": str(paths.db_path),
                "analysis_result_id": row_id,
                "latest_analysis": latest,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def cmd_refresh_prices() -> int:
    paths = discover_paths()
    repository = InvestmentRepository(paths.db_path, paths.schema_path)
    repository.initialize()
    portfolio_state = load_portfolio_state(paths.portfolio_state_path)
    asset_codes = [asset.theme or asset.name for asset in portfolio_state.assets]
    primary = JsonFileMarketDataProvider("mock-primary", paths.market_data_primary_path)
    backup = JsonFileMarketDataProvider("mock-backup", paths.market_data_backup_path)
    refresh_result = refresh_market_quotes(asset_codes, primary, backup)
    inserted = 0
    if refresh_result["status"] == "success":
        quotes = [MarketQuote.from_dict(item, default_source=str(refresh_result["source"])) for item in refresh_result["quotes"]]
        inserted = repository.store_price_snapshots(quotes)
    print(
        json.dumps(
            {
                "db_path": str(paths.db_path),
                "refresh_result": refresh_result,
                "inserted_rows": inserted,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if refresh_result["status"] == "success" else 1


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "init-db":
        return cmd_init_db()
    if args.command == "portfolio-summary":
        return cmd_portfolio_summary()
    if args.command == "rebalance-check":
        return cmd_rebalance_check()
    if args.command == "persist-analysis":
        return cmd_persist_analysis()
    if args.command == "refresh-prices":
        return cmd_refresh_prices()

    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
