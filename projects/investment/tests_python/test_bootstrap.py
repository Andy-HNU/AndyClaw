from __future__ import annotations

import importlib.util
import sqlite3
import types
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import pandas as pd

from investment_agent.config import discover_paths
from investment_agent.db.repository import InvestmentRepository
from investment_agent.models.portfolio import Asset, PortfolioState
from investment_agent.providers import (
    FailingMarketDataProvider,
    FailingNewsDataProvider,
    JsonFileMarketDataProvider,
    JsonFileNewsDataProvider,
    build_default_market_data_chain,
    build_default_news_data_chain,
    build_provider_capabilities,
    refresh_market_quotes,
    refresh_news_items,
)
from investment_agent.providers.factory import AkshareMarketProvider, AkshareNewsProvider
from investment_agent.services.monthly_planner import build_monthly_plan
from investment_agent.services.rebalance_recorder import persist_rebalance_review
from investment_agent.services.portfolio_analyzer import (
    build_portfolio_analysis,
    calculate_allocations,
    load_target_allocation,
    load_portfolio_state,
)
from investment_agent.services.rebalancing_engine import evaluate_rebalance
from investment_agent.services.report_generator import generate_monthly_report
from investment_agent.services.report_generator import generate_weekly_report
from investment_agent.services.signal_engine import (
    PriceBar,
    assess_asset_signals,
    build_asset_signal_review,
    build_position_change_summary,
    compute_ad_line,
    compute_cmf,
    compute_obv_line,
    compute_volume_ratio,
    load_asset_research,
)
from investment_agent.workflows.monthly_review import run_monthly_review
from investment_agent.workflows.weekly_review import run_weekly_review


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
        assets = self.repository.fetch_portfolio_assets()
        self.assertGreaterEqual(len(assets), 1)
        self.assertIsNotNone(assets[0]["quantity"])

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

    def test_workspace_portfolio_state_includes_shares_and_average_cost(self) -> None:
        state = load_portfolio_state(self.paths.portfolio_state_path)
        by_code = {asset.theme or asset.name: asset for asset in state.assets}
        self.assertAlmostEqual(by_code["power_grid"].shares, 2050.0089, places=4)
        self.assertAlmostEqual(by_code["power_grid"].average_cost, 1.03, places=2)
        self.assertEqual(by_code["power_grid"].asset_type, "etf")
        self.assertAlmostEqual(by_code["黄金"].shares, 20.0295, places=4)

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

    def test_akshare_market_provider_standardizes_etf_fund_and_fixture_quotes(self) -> None:
        provider = AkshareMarketProvider(self.paths)
        fake_module = types.SimpleNamespace(
            spot_hist_sge=lambda symbol: pd.DataFrame(
                [{"date": "2026-03-10", "open": 1139.1, "close": 1144.78, "low": 1132.1, "high": 1151.6}]
            ),
            fund_etf_spot_em=lambda: pd.DataFrame(
                [
                    {
                        "代码": "561200",
                        "名称": "电网指数",
                        "最新价": 1.127,
                        "最高价": 1.133,
                        "最低价": 1.119,
                        "成交量": 1502300,
                        "更新时间": "2026-03-10 15:00:00",
                    }
                ]
            ),
            fund_value_estimation_em=lambda symbol="全部": pd.DataFrame(
                [
                    {
                        "基金代码": "003376",
                        "基金名称": "广发中债7-10年国开债指数A",
                        "2026-03-10-估算数据-估算值": 1.3451,
                        "2026-03-10-公布数据-单位净值": 1.3449,
                    }
                ]
            ),
        )

        with mock.patch("importlib.import_module", return_value=fake_module):
            quotes = provider.get_latest_quotes(["power_grid", "广发中债7-10年", "黄金", "现金"])

        by_code = {item.asset_code: item for item in quotes}
        self.assertEqual(by_code["power_grid"].source, "akshare-market")
        self.assertAlmostEqual(by_code["广发中债7-10年"].close_price, 1.3451, places=4)
        self.assertEqual(by_code["黄金"].source, "akshare-market")
        self.assertAlmostEqual(by_code["黄金"].close_price, 1144.78, places=2)
        self.assertEqual(by_code["现金"].close_price, 1.0)

    def test_akshare_news_provider_standardizes_keyword_and_macro_news(self) -> None:
        provider = AkshareNewsProvider(self.paths)
        fake_module = types.SimpleNamespace(
            stock_news_em=lambda symbol: pd.DataFrame(
                [
                    {
                        "关键词": symbol,
                        "新闻标题": f"{symbol} 新闻标题",
                        "新闻内容": f"{symbol} 新闻摘要",
                        "发布时间": "2026-03-10 12:00:00",
                        "文章来源": "东财",
                        "新闻链接": f"https://example.com/{symbol}",
                    }
                ]
            ),
            stock_news_main_cx=lambda: pd.DataFrame(
                [{"tag": "市场动态", "summary": "宏观摘要", "url": "https://example.com/2026-03-10/cx"}]
            ),
        )

        with mock.patch("importlib.import_module", return_value=fake_module):
            items = provider.get_latest_news(limit=4)

        self.assertGreaterEqual(len(items), 3)
        self.assertEqual(items[0].source, "akshare-news")
        self.assertTrue(any(item.source == "akshare-news-caixin" for item in items))

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

    def test_rebalance_review_can_be_persisted(self) -> None:
        analysis = build_portfolio_analysis(
            self.paths.portfolio_state_path, self.paths.target_allocation_path
        )
        targets = load_target_allocation(self.paths.target_allocation_path)
        rebalance_result = evaluate_rebalance(analysis["allocations_pct"], targets)
        self.repository.initialize()

        persisted = persist_rebalance_review(self.repository, analysis, rebalance_result)

        self.assertGreater(persisted["suggestion_id"], 0)
        self.assertEqual(len(persisted["risk_signal_ids"]), len(rebalance_result["breaches"]))
        latest_suggestion = self.repository.fetch_latest_investment_suggestion()
        self.assertIsNotNone(latest_suggestion)
        self.assertEqual(latest_suggestion["suggestion_type"], "rebalance_review")
        self.assertEqual(latest_suggestion["status"], "ready")
        signals = self.repository.fetch_open_risk_signals()
        self.assertGreaterEqual(len(signals), 1)
        self.assertEqual(signals[0]["signal_type"], "allocation_drift")

    def test_news_primary_provider_writes_news_items(self) -> None:
        provider = JsonFileNewsDataProvider("mock-news-primary", self.paths.news_data_primary_path)

        refresh_result = refresh_news_items(provider, limit=5)
        items = provider.get_latest_news(limit=5)

        self.assertEqual(refresh_result["status"], "success")
        self.repository.initialize()
        inserted = self.repository.store_news_items(items)
        self.assertEqual(inserted, 5)
        latest_news = self.repository.fetch_recent_news(limit=2)
        self.assertEqual(len(latest_news), 2)
        self.assertEqual(latest_news[0]["topic"], "政策")

    def test_news_falls_back_to_backup_provider(self) -> None:
        primary = FailingNewsDataProvider("mock-news-primary", "simulated upstream timeout")
        backup = JsonFileNewsDataProvider("mock-news-backup", self.paths.news_data_backup_path)

        refresh_result = refresh_news_items(primary, backup, limit=2)

        self.assertEqual(refresh_result["status"], "success")
        self.assertTrue(refresh_result["used_backup"])
        self.assertEqual(refresh_result["source"], "mock-news-backup")

    def test_position_change_summary_splits_price_and_flow_effects(self) -> None:
        current_state = load_portfolio_state(self.paths.portfolio_state_path)
        previous_state = load_portfolio_state(self.paths.previous_portfolio_state_path)

        summary = build_position_change_summary(current_state, previous_state)
        by_code = {item["asset_code"]: item for item in summary}

        self.assertAlmostEqual(by_code["power_grid"]["amount_change"], 164.96, places=2)
        self.assertAlmostEqual(by_code["power_grid"]["share_change"], 100.0, places=4)
        self.assertAlmostEqual(by_code["power_grid"]["flow_effect"], 112.7, places=2)
        self.assertAlmostEqual(by_code["现金"]["share_change"], -1800.0, places=4)
        self.assertAlmostEqual(by_code["现金"]["amount_change"], -1800.0, places=2)

    def test_signal_formula_helpers_match_expected_sequences(self) -> None:
        bars = [
            PriceBar(close=10.8, high=11, low=9, volume=100),
            PriceBar(close=11.4, high=11.5, low=10.5, volume=120),
            PriceBar(close=10.2, high=11, low=10, volume=90),
            PriceBar(close=12.3, high=12.5, low=11.5, volume=160),
        ]

        self.assertEqual(compute_ad_line(bars), [80.0, 176.0, 122.0, 218.0])
        self.assertEqual(compute_obv_line(bars), [0.0, 120.0, 30.0, 190.0])
        self.assertAlmostEqual(compute_cmf(bars, window=4), 0.4638, places=4)
        self.assertAlmostEqual(compute_volume_ratio(bars, window=3), 1.5484, places=4)

    def test_asset_signal_review_emits_distribution_and_valuation_signals(self) -> None:
        state = load_portfolio_state(self.paths.portfolio_state_path)
        previous_state = load_portfolio_state(self.paths.previous_portfolio_state_path)
        research = load_asset_research(self.paths.asset_research_path)

        review = build_asset_signal_review(state, previous_state, research)
        signal_names = {item["signal_name"] for item in review["signals"]}

        self.assertIn("suspected_distribution", signal_names)
        self.assertIn("valuation_premium_warning", signal_names)
        self.assertIn("manager_style_drift", signal_names)
        self.assertGreaterEqual(len(review["research_highlights"]), 3)

    def test_assess_asset_signals_handles_asset_research_fixture(self) -> None:
        state = load_portfolio_state(self.paths.portfolio_state_path)
        asset = next(item for item in state.assets if (item.theme or item.name) == "ai")
        research = load_asset_research(self.paths.asset_research_path)["ai"]

        signals = assess_asset_signals(asset, research)
        by_name = {item["signal_name"]: item for item in signals}

        self.assertEqual(by_name["suspected_distribution"]["severity"], "high")
        self.assertEqual(by_name["valuation_premium_warning"]["severity"], "high")

    def test_monthly_plan_prioritizes_underweight_assets(self) -> None:
        analysis = build_portfolio_analysis(
            self.paths.portfolio_state_path, self.paths.target_allocation_path
        )
        targets = load_target_allocation(self.paths.target_allocation_path)

        plan = build_monthly_plan(analysis, targets, monthly_budget=12000)

        self.assertAlmostEqual(analysis["total_value"], 51653.71, places=2)
        self.assertAlmostEqual(analysis["allocations_pct"]["stock"], 26.5291, places=4)
        self.assertAlmostEqual(analysis["allocations_pct"]["bond"], 23.3236, places=4)
        self.assertAlmostEqual(analysis["allocations_pct"]["gold"], 26.9156, places=4)
        self.assertAlmostEqual(analysis["allocations_pct"]["cash"], 23.2316, places=4)
        self.assertAlmostEqual(targets["stock"], 0.5, places=4)
        self.assertAlmostEqual(targets["bond"], 0.25, places=4)
        self.assertAlmostEqual(targets["gold"], 0.15, places=4)
        self.assertAlmostEqual(targets["cash"], 0.1, places=4)
        self.assertEqual(plan["status"], "needs_repair")
        self.assertEqual(plan["underweight_categories"], ["stock", "bond"])
        self.assertAlmostEqual(
            sum(item["recommended_amount"] for item in plan["recommendations"]),
            12000.0,
            places=2,
        )
        self.assertEqual(plan["recommendations"][0]["category"], "stock")
        self.assertAlmostEqual(plan["recommendations"][0]["gap_value"], 12123.59, places=2)
        self.assertAlmostEqual(plan["recommendations"][0]["recommended_amount"], 11200.04, places=2)
        self.assertEqual(plan["recommendations"][1]["category"], "bond")
        self.assertAlmostEqual(plan["recommendations"][1]["gap_value"], 865.92, places=2)
        self.assertAlmostEqual(plan["recommendations"][1]["recommended_amount"], 799.96, places=2)
        self.assertEqual(plan["remaining_budget"], 0.0)

    def test_monthly_report_includes_position_and_research_sections(self) -> None:
        analysis = build_portfolio_analysis(
            self.paths.portfolio_state_path, self.paths.target_allocation_path
        )
        current_state = load_portfolio_state(self.paths.portfolio_state_path)
        previous_state = load_portfolio_state(self.paths.previous_portfolio_state_path)
        research = load_asset_research(self.paths.asset_research_path)
        review = build_asset_signal_review(current_state, previous_state, research)
        targets = load_target_allocation(self.paths.target_allocation_path)
        report = generate_monthly_report(
            analysis=analysis,
            rebalance_result=evaluate_rebalance(analysis["allocations_pct"], targets),
            monthly_plan=build_monthly_plan(analysis, targets, monthly_budget=12000),
            risk_signals=review["signals"],
            news_items=[],
            position_changes=review["positions"],
            research_highlights=review["research_highlights"],
        )

        self.assertIn("position_changes", report["content_json"])
        self.assertIn("research_highlights", report["content_json"])
        self.assertEqual(report["content_json"]["schema_version"], "1.0")
        self.assertEqual(report["content_json"]["sections"][0]["section_id"], "portfolio_snapshot")
        self.assertIn("细分持仓变化", report["content_md"])
        self.assertIn("资产研究摘要", report["content_md"])

    def test_weekly_report_uses_stable_schema_sections(self) -> None:
        analysis = build_portfolio_analysis(
            self.paths.portfolio_state_path, self.paths.target_allocation_path
        )
        current_state = load_portfolio_state(self.paths.portfolio_state_path)
        previous_state = load_portfolio_state(self.paths.previous_portfolio_state_path)
        research = load_asset_research(self.paths.asset_research_path)
        review = build_asset_signal_review(current_state, previous_state, research)
        report = generate_weekly_report(
            analysis=analysis,
            position_changes=review["positions"],
            risk_signals=review["signals"],
            news_items=[],
        )

        self.assertEqual(report["report_type"], "weekly")
        self.assertEqual(report["content_json"]["schema_version"], "1.0")
        section_ids = [item["section_id"] for item in report["content_json"]["sections"]]
        self.assertEqual(
            section_ids,
            ["portfolio_snapshot", "position_changes", "risk_summary", "news_summary", "watchlist"],
        )
        self.assertIn("本周仓位快照", report["content_md"])

    def test_weekly_review_workflow_persists_weekly_report(self) -> None:
        self.repository.initialize()

        result = run_weekly_review(self.paths, self.repository, news_limit=5)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["price_refresh"]["status"], "success")
        self.assertEqual(result["news_refresh"]["status"], "success")
        latest_report = self.repository.fetch_latest_report("weekly")
        self.assertIsNotNone(latest_report)
        self.assertEqual(latest_report["report_type"], "weekly")
        self.assertEqual(latest_report["content_json"]["schema_version"], "1.0")
        self.assertIn("position_changes", latest_report["content_json"])

    def test_monthly_review_workflow_persists_report_and_supporting_data(self) -> None:
        self.repository.initialize()

        result = run_monthly_review(self.paths, self.repository, news_limit=5, monthly_budget=12000)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["price_refresh"]["status"], "success")
        self.assertEqual(result["news_refresh"]["status"], "success")
        self.assertGreater(self.repository.count_rows("price_snapshots"), 0)
        self.assertGreater(self.repository.count_rows("news_items"), 0)
        self.assertGreater(self.repository.count_rows("reports"), 0)
        self.assertGreaterEqual(len(result["signal_review"]["signals"]), 3)
        latest_report = self.repository.fetch_latest_report("monthly")
        self.assertIsNotNone(latest_report)
        self.assertEqual(latest_report["report_type"], "monthly")
        self.assertIn("news_observations", latest_report["content_json"])
        self.assertIn("monthly_plan", latest_report["content_json"])
        self.assertIn("position_changes", latest_report["content_json"])
        self.assertIn("research_highlights", latest_report["content_json"])
        self.assertGreaterEqual(len(self.repository.fetch_open_risk_signals()), 4)

    def test_provider_capabilities_reflect_current_environment(self) -> None:
        capabilities = build_provider_capabilities(self.paths)
        by_name = {item.name: item for item in capabilities}

        self.assertEqual(by_name["akshare-market"].enabled, importlib.util.find_spec("akshare") is not None)
        self.assertEqual(by_name["akshare-news"].enabled, importlib.util.find_spec("akshare") is not None)
        self.assertFalse(by_name["efinance-fund"].enabled)
        self.assertTrue(by_name["mock-primary"].enabled)
        self.assertTrue(by_name["mock-backup"].enabled)

    def test_default_chains_prioritize_akshare_when_available(self) -> None:
        market_chain = build_default_market_data_chain(self.paths)
        news_chain = build_default_news_data_chain(self.paths)
        if importlib.util.find_spec("akshare") is not None:
            self.assertEqual(market_chain[0].__class__.__name__, "AkshareMarketProvider")
            self.assertEqual(news_chain[0].__class__.__name__, "AkshareNewsProvider")
        else:
            self.assertEqual(market_chain[0].__class__.__name__, "JsonFileMarketDataProvider")
            self.assertEqual(news_chain[0].__class__.__name__, "JsonFileNewsDataProvider")


if __name__ == "__main__":
    unittest.main()
