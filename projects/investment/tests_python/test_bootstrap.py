from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from investment_agent.config import discover_paths
from investment_agent.db.repository import InvestmentRepository
from investment_agent.models.portfolio import Asset, PortfolioState
from investment_agent.providers import (
    FailingMarketDataProvider,
    JsonFileMarketDataProvider,
    refresh_market_quotes,
)
from investment_agent.services.portfolio_analyzer import (
    build_portfolio_analysis,
    calculate_allocations,
    load_target_allocation,
    load_portfolio_state,
)
from investment_agent.services.rebalancing_engine import evaluate_rebalance


class InvestmentBootstrapTests(unittest.TestCase):
    def setUp(self) -> None:
        self.paths = discover_paths()
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tempdir.name) / "investment.db"
        self.repository = InvestmentRepository(self.db_path, self.paths.schema_path)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_initialize_and_seed_sqlite(self) -> None:
        state = load_portfolio_state(self.paths.portfolio_state_path)
        self.repository.initialize()
        self.repository.seed_portfolio_state(state)

        self.assertTrue(self.db_path.exists())
        self.assertGreaterEqual(self.repository.count_rows("portfolio_assets"), 1)
        self.assertGreaterEqual(self.repository.count_rows("portfolio_snapshots"), 1)

        latest = self.repository.fetch_latest_snapshot()
        self.assertIsNotNone(latest)
        self.assertEqual(latest["snapshot_time"], "2026-03")

        with sqlite3.connect(self.db_path) as connection:
            row = connection.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='reports'"
            ).fetchone()
        self.assertEqual(row[0], 1)

    def test_portfolio_ratio_matches_spec(self) -> None:
        sample_state = PortfolioState(
            updated_at="spec-case",
            assets=[
                Asset(name="黄金", category="gold", value=10000),
                Asset(name="债券", category="bond", value=10000),
                Asset(name="股票", category="stock", value=20000),
                Asset(name="现金", category="cash", value=0),
            ],
        )
        allocations = calculate_allocations(sample_state)
        self.assertAlmostEqual(sample_state.total_value, 40000, places=2)
        self.assertAlmostEqual(allocations["gold"], 25.0, places=3)
        self.assertAlmostEqual(allocations["bond"], 25.0, places=3)
        self.assertAlmostEqual(allocations["stock"], 50.0, places=3)
        self.assertAlmostEqual(allocations["cash"], 0.0, places=3)

    def test_current_portfolio_summary_runs_against_workspace_data(self) -> None:
        analysis = build_portfolio_analysis(
            self.paths.portfolio_state_path, self.paths.target_allocation_path
        )
        self.assertAlmostEqual(analysis["total_value"], 51653.71, places=2)
        allocations = analysis["allocations_pct"]
        self.assertSetEqual(set(allocations), {"gold", "bond", "stock", "cash"})
        self.assertAlmostEqual(sum(allocations.values()), 100.0, places=2)

    def test_rebalance_trigger_matches_rule_doc(self) -> None:
        result = evaluate_rebalance(
            allocations_pct={"stock": 70.0, "bond": 10.0, "gold": 10.0, "cash": 10.0},
            targets={"stock": 0.5, "bond": 0.25, "gold": 0.15, "cash": 0.1},
            threshold_pct=10.0,
        )
        self.assertTrue(result["triggered"])
        self.assertEqual(result["breaches"][0]["category"], "stock")
        self.assertEqual(result["breaches"][0]["upper_bound_pct"], 60.0)
        self.assertEqual(
            result["priority_action"],
            "use new funds to repair underweight allocations before considering sells",
        )

    def test_current_workspace_rebalance_check_runs(self) -> None:
        analysis = build_portfolio_analysis(
            self.paths.portfolio_state_path, self.paths.target_allocation_path
        )
        targets = load_target_allocation(self.paths.target_allocation_path)
        result = evaluate_rebalance(analysis["allocations_pct"], targets)
        self.assertIn("triggered", result)
        self.assertIn("breaches", result)

    def test_market_data_primary_provider_writes_price_snapshots(self) -> None:
        state = load_portfolio_state(self.paths.portfolio_state_path)
        asset_codes = [asset.theme or asset.name for asset in state.assets]
        provider = JsonFileMarketDataProvider(
            "mock-primary", self.paths.market_data_primary_path
        )

        refresh_result = refresh_market_quotes(asset_codes, provider)
        quotes = provider.get_latest_quotes(asset_codes)

        self.assertEqual(refresh_result["status"], "success")
        self.assertFalse(refresh_result["used_backup"])
        self.repository.initialize()
        inserted = self.repository.store_price_snapshots(quotes)
        self.assertEqual(inserted, len(asset_codes))
        latest = self.repository.fetch_latest_price_snapshot("ai")
        self.assertIsNotNone(latest)
        self.assertEqual(latest["source"], "mock-primary")

    def test_market_data_falls_back_to_backup_provider(self) -> None:
        state = load_portfolio_state(self.paths.portfolio_state_path)
        asset_codes = [asset.theme or asset.name for asset in state.assets]
        primary = FailingMarketDataProvider("mock-primary", "simulated upstream timeout")
        backup = JsonFileMarketDataProvider("mock-backup", self.paths.market_data_backup_path)

        refresh_result = refresh_market_quotes(asset_codes, primary, backup)

        self.assertEqual(refresh_result["status"], "success")
        self.assertTrue(refresh_result["used_backup"])
        self.assertEqual(refresh_result["source"], "mock-backup")
        self.assertEqual(refresh_result["errors"][0]["source"], "mock-primary")

    def test_market_data_reports_failure_if_all_sources_fail(self) -> None:
        state = load_portfolio_state(self.paths.portfolio_state_path)
        asset_codes = [asset.theme or asset.name for asset in state.assets]
        primary = FailingMarketDataProvider("mock-primary", "simulated upstream timeout")
        backup = FailingMarketDataProvider("mock-backup", "simulated backup timeout")

        refresh_result = refresh_market_quotes(asset_codes, primary, backup)

        self.assertEqual(refresh_result["status"], "failed")
        self.assertEqual(len(refresh_result["errors"]), 2)
        self.assertEqual(refresh_result["message"], "all configured market data providers failed")

    def test_analysis_result_can_be_persisted(self) -> None:
        analysis = build_portfolio_analysis(
            self.paths.portfolio_state_path, self.paths.target_allocation_path
        )
        self.repository.initialize()
        row_id = self.repository.store_analysis_result(analysis)

        self.assertGreater(row_id, 0)
        latest = self.repository.fetch_latest_analysis()
        self.assertIsNotNone(latest)
        self.assertEqual(latest["analysis_time"], "2026-03")
        self.assertIn("gold", latest["allocation_json"])
        self.assertIn("cash", latest["deviation_json"])


if __name__ == "__main__":
    unittest.main()
