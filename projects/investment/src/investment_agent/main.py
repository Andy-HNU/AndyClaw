from __future__ import annotations

import argparse
import json

from investment_agent.config import discover_paths
from investment_agent.db.repository import InvestmentRepository
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


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "init-db":
        return cmd_init_db()
    if args.command == "portfolio-summary":
        return cmd_portfolio_summary()
    if args.command == "rebalance-check":
        return cmd_rebalance_check()

    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
