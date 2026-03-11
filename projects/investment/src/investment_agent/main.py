from __future__ import annotations

import argparse
import json
from pathlib import Path

from investment_agent.config import discover_paths
from investment_agent.db.repository import InvestmentRepository
from investment_agent.providers import (
    MarketQuote,
    build_default_market_data_chain,
    build_provider_capabilities,
    refresh_market_quotes,
)
from investment_agent.services.monthly_planner import build_monthly_plan
from investment_agent.services.intraday_proxy_engine import build_intraday_proxy_review
from investment_agent.services.ocr_importer import build_ocr_portfolio_import
from investment_agent.services.portfolio_analyzer import (
    build_portfolio_analysis,
    load_target_allocation,
    load_portfolio_state,
)
from investment_agent.services.rebalance_recorder import persist_rebalance_review
from investment_agent.services.rebalancing_engine import evaluate_rebalance
from investment_agent.services.signal_engine import build_asset_signal_review, load_asset_research
from investment_agent.services.snapshot_importer import build_snapshot_import
from investment_agent.workflows.daily_review import run_daily_review
from investment_agent.workflows.weekly_review import run_weekly_review
from investment_agent.workflows.monthly_review import run_monthly_review


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Investment agent utilities")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init-db", help="Initialize SQLite and seed first snapshot")
    subparsers.add_parser("portfolio-summary", help="Print current portfolio summary")
    subparsers.add_parser("rebalance-check", help="Evaluate rebalance trigger")
    subparsers.add_parser("persist-analysis", help="Persist the current portfolio analysis")
    subparsers.add_parser("refresh-prices", help="Refresh latest price snapshots with fallback")
    subparsers.add_parser("persist-rebalance", help="Persist the current rebalance review")
    subparsers.add_parser("provider-capabilities", help="Show available market-data adapters")
    subparsers.add_parser("monthly-plan", help="Generate the current monthly investment plan")
    subparsers.add_parser("signal-review", help="Generate asset-level V2 signal and position review")
    subparsers.add_parser("daily-review", help="Run the daily review workflow")
    subparsers.add_parser("weekly-review", help="Run the weekly review workflow")
    subparsers.add_parser("monthly-review", help="Run the monthly review workflow")
    cleanup_parser = subparsers.add_parser(
        "cleanup-legacy-duplicates",
        help="Cleanup pre-idempotency same-day duplicate open risk signals/suggestions/reports",
    )
    cleanup_parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply deletions (default is dry-run preview)",
    )
    import_parser = subparsers.add_parser("import-snapshot", help="Import portfolio screenshots with vision-first fallback")
    import_parser.add_argument("--portfolio-image", help="Path to the holdings overview screenshot")
    import_parser.add_argument("--gold-image", help="Path to the gold position screenshot")
    ocr_parser = subparsers.add_parser("ocr-portfolio", help="OCR portfolio screenshots into structured candidates")
    ocr_parser.add_argument("--portfolio-image", help="Path to the holdings overview screenshot")
    ocr_parser.add_argument("--gold-image", help="Path to the gold position screenshot")
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
    primary, backup = build_default_market_data_chain(paths)
    refresh_result = refresh_market_quotes(asset_codes, primary, backup)
    inserted = 0
    if refresh_result["status"] == "success":
        quotes = [
            MarketQuote.from_dict(item, default_source=str(refresh_result["source"]))
            for item in refresh_result["quotes"]
        ]
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


def cmd_persist_rebalance() -> int:
    paths = discover_paths()
    repository = InvestmentRepository(paths.db_path, paths.schema_path)
    repository.initialize()
    analysis = build_portfolio_analysis(paths.portfolio_state_path, paths.target_allocation_path)
    targets = load_target_allocation(paths.target_allocation_path)
    rebalance_result = evaluate_rebalance(analysis["allocations_pct"], targets)
    persisted = persist_rebalance_review(repository, analysis, rebalance_result)
    print(
        json.dumps(
            {
                "db_path": str(paths.db_path),
                "rebalance_result": rebalance_result,
                "persisted": persisted,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def cmd_provider_capabilities() -> int:
    paths = discover_paths()
    capabilities = [item.to_dict() for item in build_provider_capabilities(paths)]
    print(json.dumps({"providers": capabilities}, ensure_ascii=False, indent=2))
    return 0


def cmd_monthly_plan() -> int:
    paths = discover_paths()
    analysis = build_portfolio_analysis(paths.portfolio_state_path, paths.target_allocation_path)
    targets = load_target_allocation(paths.target_allocation_path)
    plan = build_monthly_plan(analysis, targets)
    print(json.dumps(plan, ensure_ascii=False, indent=2))
    return 0


def cmd_monthly_review() -> int:
    paths = discover_paths()
    repository = InvestmentRepository(paths.db_path, paths.schema_path)
    result = run_monthly_review(paths, repository)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_cleanup_legacy_duplicates(apply: bool) -> int:
    paths = discover_paths()
    repository = InvestmentRepository(paths.db_path, paths.schema_path)
    repository.initialize()
    result = repository.cleanup_legacy_same_day_duplicates(dry_run=not apply)
    print(
        json.dumps(
            {
                "db_path": str(paths.db_path),
                "mode": "apply" if apply else "dry_run",
                "deleted": result,
                "command": "python3 -m investment_agent.main cleanup-legacy-duplicates --apply",
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def cmd_signal_review() -> int:
    paths = discover_paths()
    current_state = load_portfolio_state(paths.portfolio_state_path)
    previous_state = load_portfolio_state(paths.previous_portfolio_state_path)
    research = load_asset_research(paths.asset_research_path)
    review = build_asset_signal_review(current_state, previous_state, research)
    review["intraday_market"] = build_intraday_proxy_review(
        portfolio_state=current_state,
        config_path=paths.intraday_proxy_config_path,
        realtime_path=paths.intraday_realtime_path,
    )
    print(json.dumps(review, ensure_ascii=False, indent=2))
    return 0


def cmd_weekly_review() -> int:
    paths = discover_paths()
    repository = InvestmentRepository(paths.db_path, paths.schema_path)
    result = run_weekly_review(paths, repository)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_daily_review() -> int:
    paths = discover_paths()
    repository = InvestmentRepository(paths.db_path, paths.schema_path)
    result = run_daily_review(paths, repository)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def _resolve_cli_path(raw_path: str | None) -> Path | None:
    if raw_path is None:
        return None
    candidate = Path(raw_path)
    if candidate.is_absolute():
        return candidate
    return (discover_paths().project_root / candidate).resolve()


def cmd_ocr_portfolio(portfolio_image: str | None, gold_image: str | None) -> int:
    result = build_ocr_portfolio_import(
        portfolio_image_path=_resolve_cli_path(portfolio_image),
        gold_image_path=_resolve_cli_path(gold_image),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_import_snapshot(portfolio_image: str | None, gold_image: str | None) -> int:
    result = build_snapshot_import(
        portfolio_image_path=_resolve_cli_path(portfolio_image),
        gold_image_path=_resolve_cli_path(gold_image),
    )
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
    if args.command == "persist-analysis":
        return cmd_persist_analysis()
    if args.command == "refresh-prices":
        return cmd_refresh_prices()
    if args.command == "persist-rebalance":
        return cmd_persist_rebalance()
    if args.command == "provider-capabilities":
        return cmd_provider_capabilities()
    if args.command == "monthly-plan":
        return cmd_monthly_plan()
    if args.command == "signal-review":
        return cmd_signal_review()
    if args.command == "daily-review":
        return cmd_daily_review()
    if args.command == "weekly-review":
        return cmd_weekly_review()
    if args.command == "monthly-review":
        return cmd_monthly_review()
    if args.command == "cleanup-legacy-duplicates":
        return cmd_cleanup_legacy_duplicates(args.apply)
    if args.command == "import-snapshot":
        return cmd_import_snapshot(args.portfolio_image, args.gold_image)
    if args.command == "ocr-portfolio":
        return cmd_ocr_portfolio(args.portfolio_image, args.gold_image)

    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
