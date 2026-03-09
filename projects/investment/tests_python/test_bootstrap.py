from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from investment_agent.config import discover_paths
from investment_agent.db.repository import InvestmentRepository
from investment_agent.models.portfolio import Asset, PortfolioState
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


if __name__ == "__main__":
    unittest.main()
