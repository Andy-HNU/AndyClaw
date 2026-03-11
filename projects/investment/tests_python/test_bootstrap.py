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
    build_default_intraday_data_chain,
    build_default_market_data_chain,
    build_default_news_data_chain,
    build_provider_capabilities,
    refresh_intraday_proxy_inputs,
    refresh_market_quotes,
    refresh_news_items,
)
from investment_agent.providers.factory import AkshareMarketProvider, AkshareNewsProvider
from investment_agent.services.chart_artifacts import render_daily_price_chart
from investment_agent.services.intraday_proxy_engine import (
    build_intraday_proxy_review,
    classify_intraday_sentiment,
)
from investment_agent.services.monthly_planner import build_monthly_plan
from investment_agent.services.intraday_sanity import run_intraday_sentiment_sanity
from investment_agent.services.ocr_importer import (
    build_ocr_portfolio_import,
    extract_ocr_lines,
    ocr_backend_available,
    parse_gold_snapshot,
    parse_portfolio_snapshot,
)
from investment_agent.services.rebalance_recorder import persist_rebalance_review
from investment_agent.services.portfolio_analyzer import (
    build_portfolio_analysis,
    calculate_allocations,
    load_target_allocation,
    load_portfolio_state,
)
from investment_agent.services.rebalancing_engine import evaluate_rebalance
from investment_agent.services.report_generator import generate_daily_report, generate_monthly_report
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
from investment_agent.services.snapshot_importer import build_snapshot_import
from investment_agent.workflows.monthly_review import run_monthly_review
from investment_agent.workflows.daily_review import run_daily_review
from investment_agent.workflows.weekly_review import run_weekly_review


class InvestmentBootstrapTests(unittest.TestCase):
    def setUp(self) -> None:
        self.paths = discover_paths()
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tempdir.name) / "investment.db"
        self.repository = InvestmentRepository(self.db_path, self.paths.schema_path)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    @property
    def portfolio_screenshot_path(self) -> Path:
        return Path("/root/usrFile/bb560d57ad2761440ddc9b4069e96e83.jpg")

    @property
    def gold_screenshot_path(self) -> Path:
        return Path("/root/usrFile/a9c549ccf141b31d97cd81b79aa2f98c.jpg")

    def test_initialize_and_seed_sqlite(self) -> None:
        state = load_portfolio_state(self.paths.portfolio_state_path)
        self.repository.initialize()
        self.repository.seed_portfolio_state(state)

        self.assertTrue(self.db_path.exists())
        self.assertGreaterEqual(self.repository.count_rows("portfolio_assets"), 1)
        self.assertGreaterEqual(self.repository.count_rows("portfolio_snapshots"), 1)

        latest = self.repository.fetch_latest_snapshot()
        self.assertIsNotNone(latest)
        self.assertEqual(latest["snapshot_time"], "2026-03-11")
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
        self.assertAlmostEqual(analysis["total_value"], 49802.47, places=2)
        allocations = analysis["allocations_pct"]
        self.assertSetEqual(set(allocations), {"gold", "bond", "stock", "cash"})
        self.assertAlmostEqual(sum(allocations.values()), 100.0, places=2)

    def test_workspace_portfolio_state_includes_shares_and_average_cost(self) -> None:
        state = load_portfolio_state(self.paths.portfolio_state_path)
        by_code = {asset.theme or asset.name: asset for asset in state.assets}
        self.assertAlmostEqual(by_code["power_grid"].shares, 2050.0089, places=4)
        self.assertAlmostEqual(by_code["power_grid"].average_cost, 1.03, places=2)
        self.assertEqual(by_code["power_grid"].asset_type, "etf")
        self.assertAlmostEqual(by_code["黄金"].shares, 12.1713, places=4)

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
                        "代码": "025833",
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
                        "基金代码": "011062",
                        "基金名称": "广发中债7-10年期国开行债券指数E",
                        "2026-03-10-估算数据-估算值": 1.0413,
                        "2026-03-10-公布数据-单位净值": 1.0408,
                    }
                ]
            ),
        )

        with mock.patch("importlib.import_module", return_value=fake_module):
            quotes = provider.get_latest_quotes(["power_grid", "广发中债7-10年期国开行债券指数E", "黄金", "现金"])

        by_code = {item.asset_code: item for item in quotes}
        self.assertEqual(by_code["power_grid"].source, "akshare-market")
        self.assertAlmostEqual(by_code["广发中债7-10年期国开行债券指数E"].close_price, 1.0413, places=4)
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
        self.assertEqual(latest["analysis_time"], "2026-03-11")
        self.assertIn("gold", latest["allocation_json"])
        self.assertIn("cash", latest["deviation_json"])

    def test_store_report_updates_existing_same_day_report(self) -> None:
        self.repository.initialize()
        first_id = self.repository.store_report(
            report_time="2026-03-11",
            report_type="daily",
            title="first",
            content_md="one",
            content_json={"v": 1},
        )
        second_id = self.repository.store_report(
            report_time="2026-03-11 20:01:00",
            report_type="daily",
            title="second",
            content_md="two",
            content_json={"v": 2},
        )

        self.assertEqual(first_id, second_id)
        self.assertEqual(self.repository.count_rows("reports"), 1)
        latest = self.repository.fetch_latest_report("daily")
        self.assertEqual(latest["title"], "second")
        self.assertEqual(latest["content_json"]["v"], 2)
        self.assertEqual(latest["report_time"], "2026-03-11 20:01:00")

    def test_store_investment_suggestion_is_idempotent_within_same_day(self) -> None:
        self.repository.initialize()
        first_id = self.repository.store_investment_suggestion(
            suggestion_time="2026-03-11 09:30:00",
            suggestion_type="rebalance_review",
            content={"v": 1},
            rationale="first",
            status="draft",
        )
        second_id = self.repository.store_investment_suggestion(
            suggestion_time="2026-03-11 16:40:00",
            suggestion_type="rebalance_review",
            content={"v": 2},
            rationale="second",
            status="ready",
        )

        self.assertEqual(first_id, second_id)
        self.assertEqual(self.repository.count_rows("investment_suggestions"), 1)
        latest = self.repository.fetch_latest_investment_suggestion()
        self.assertIsNotNone(latest)
        self.assertEqual(latest["content_json"]["v"], 2)
        self.assertEqual(latest["status"], "ready")

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

    def test_rebalance_review_dedupes_same_day_open_signals(self) -> None:
        analysis = build_portfolio_analysis(
            self.paths.portfolio_state_path, self.paths.target_allocation_path
        )
        targets = load_target_allocation(self.paths.target_allocation_path)
        rebalance_result = evaluate_rebalance(analysis["allocations_pct"], targets)
        self.repository.initialize()

        persist_rebalance_review(self.repository, analysis, rebalance_result)
        persist_rebalance_review(self.repository, analysis, rebalance_result)

        open_signals = [
            item for item in self.repository.fetch_open_risk_signals() if item["signal_time"] == "2026-03-11"
        ]
        self.assertEqual(len(open_signals), len(rebalance_result["breaches"]))

    def test_store_risk_signal_dedupes_same_day_equivalent_open_signal(self) -> None:
        self.repository.initialize()
        first_id = self.repository.store_risk_signal(
            signal_time="2026-03-11 09:00:00",
            signal_type="allocation_drift",
            severity="medium",
            message="stock is over target",
            evidence={"source": "first"},
            status="open",
        )
        second_id = self.repository.store_risk_signal(
            signal_time="2026-03-11 15:00:00",
            signal_type="allocation_drift",
            severity="medium",
            message="stock is over target",
            evidence={"source": "second"},
            status="open",
        )

        self.assertEqual(first_id, second_id)
        self.assertEqual(self.repository.count_rows("risk_signals"), 1)
        open_signals = self.repository.fetch_open_risk_signals()
        self.assertEqual(open_signals[0]["signal_time"], "2026-03-11 15:00:00")
        self.assertEqual(open_signals[0]["evidence_json"]["source"], "second")

    def test_store_risk_signal_uses_semantic_dedupe_key_when_wording_changes(self) -> None:
        self.repository.initialize()
        evidence_first = {
            "breach": {"category": "stock", "current_pct": 66.1, "target_pct": 50.0},
            "priority_action": "buy bonds",
        }
        evidence_second = {
            "priority_action": "buy bonds",
            "breach": {"target_pct": 50.0, "category": "stock", "current_pct": 66.1},
        }
        first_id = self.repository.store_risk_signal(
            signal_time="2026-03-11 09:00:00",
            signal_type="allocation_drift",
            severity="high",
            message="stock allocation drifts above target",
            evidence=evidence_first,
            status="open",
        )
        second_id = self.repository.store_risk_signal(
            signal_time="2026-03-11 15:00:00",
            signal_type="allocation_drift",
            severity="high",
            message="stock allocation remains above target band",
            evidence=evidence_second,
            status="open",
        )

        self.assertEqual(first_id, second_id)
        self.assertEqual(self.repository.count_rows("risk_signals"), 1)

    def test_cleanup_legacy_duplicates_removes_pre_idempotency_rows(self) -> None:
        self.repository.initialize()
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                "INSERT INTO risk_signals(signal_time, signal_type, severity, message, evidence_json, status) VALUES (?, ?, ?, ?, ?, ?)",
                ("2026-03-10 09:00:00", "allocation_drift", "medium", "a", "{}", "open"),
            )
            connection.execute(
                "INSERT INTO risk_signals(signal_time, signal_type, severity, message, evidence_json, status) VALUES (?, ?, ?, ?, ?, ?)",
                ("2026-03-10 10:00:00", "allocation_drift", "high", "b", "{}", "open"),
            )
            connection.execute(
                "INSERT INTO investment_suggestions(suggestion_time, suggestion_type, content_json, rationale, status) VALUES (?, ?, ?, ?, ?)",
                ("2026-03-10 09:00:00", "rebalance_review", "{}", "r1", "draft"),
            )
            connection.execute(
                "INSERT INTO investment_suggestions(suggestion_time, suggestion_type, content_json, rationale, status) VALUES (?, ?, ?, ?, ?)",
                ("2026-03-10 11:00:00", "rebalance_review", "{}", "r2", "ready"),
            )
            connection.execute(
                "INSERT INTO reports(report_time, report_type, title, content_md, content_json) VALUES (?, ?, ?, ?, ?)",
                ("2026-03-10 09:00:00", "daily", "old", "x", "{}"),
            )
            connection.execute(
                "INSERT INTO reports(report_time, report_type, title, content_md, content_json) VALUES (?, ?, ?, ?, ?)",
                ("2026-03-10 12:00:00", "daily", "new", "y", "{}"),
            )
            connection.commit()

        dry_run = self.repository.cleanup_legacy_same_day_duplicates(dry_run=True)
        self.assertEqual(dry_run["total_deleted"], 3)
        self.assertEqual(self.repository.count_rows("risk_signals"), 2)

        applied = self.repository.cleanup_legacy_same_day_duplicates(dry_run=False)
        self.assertEqual(applied["total_deleted"], 3)
        self.assertEqual(self.repository.count_rows("risk_signals"), 1)
        self.assertEqual(self.repository.count_rows("investment_suggestions"), 1)
        self.assertEqual(self.repository.count_rows("reports"), 1)

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

        self.assertAlmostEqual(by_code["黄金"]["amount_change"], 13996.26, places=2)
        self.assertAlmostEqual(by_code["黄金"]["share_change"], 12.1713, places=4)
        self.assertAlmostEqual(by_code["power_grid"]["amount_change"], 54.21, places=2)
        self.assertAlmostEqual(by_code["power_grid"]["share_change"], 0.0, places=4)
        self.assertAlmostEqual(by_code["power_grid"]["flow_effect"], 0.09, places=2)
        self.assertAlmostEqual(by_code["现金"]["share_change"], -2061.21, places=4)
        self.assertAlmostEqual(by_code["现金"]["amount_change"], -2061.21, places=2)

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

        self.assertAlmostEqual(analysis["total_value"], 49802.47, places=2)
        self.assertAlmostEqual(analysis["allocations_pct"]["stock"], 27.7722, places=4)
        self.assertAlmostEqual(analysis["allocations_pct"]["bond"], 24.1678, places=4)
        self.assertAlmostEqual(analysis["allocations_pct"]["gold"], 28.1035, places=4)
        self.assertAlmostEqual(analysis["allocations_pct"]["cash"], 19.9564, places=4)
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
        self.assertAlmostEqual(plan["recommendations"][0]["gap_value"], 11069.99, places=2)
        self.assertAlmostEqual(plan["recommendations"][0]["recommended_amount"], 11566.93, places=2)
        self.assertEqual(plan["recommendations"][1]["category"], "bond")
        self.assertAlmostEqual(plan["recommendations"][1]["recommended_amount"], 433.07, places=2)
        self.assertAlmostEqual(plan["recommendations"][1]["gap_value"], 414.46, places=2)
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

    def test_daily_report_uses_stable_schema_sections(self) -> None:
        analysis = build_portfolio_analysis(
            self.paths.portfolio_state_path, self.paths.target_allocation_path
        )
        current_state = load_portfolio_state(self.paths.portfolio_state_path)
        previous_state = load_portfolio_state(self.paths.previous_portfolio_state_path)
        research = load_asset_research(self.paths.asset_research_path)
        review = build_asset_signal_review(current_state, previous_state, research)
        targets = load_target_allocation(self.paths.target_allocation_path)
        report = generate_daily_report(
            analysis=analysis,
            rebalance_result=evaluate_rebalance(analysis["allocations_pct"], targets),
            risk_signals=review["signals"],
            news_items=[],
            chart_artifacts=[],
        )

        self.assertEqual(report["report_type"], "daily")
        self.assertEqual(report["content_json"]["schema_version"], "1.0")
        section_ids = [item["section_id"] for item in report["content_json"]["sections"]]
        self.assertEqual(
            section_ids,
            [
                "portfolio_snapshot",
                "trend_charts",
                "rebalance_review",
                "risk_summary",
                "news_summary",
                "action_items",
            ],
        )
        self.assertIn("今日仓位快照", report["content_md"])
        self.assertIn("chart_artifacts", report["content_json"])

    def test_intraday_proxy_review_uses_holdings_and_fallback_paths(self) -> None:
        current_state = load_portfolio_state(self.paths.portfolio_state_path)

        review = build_intraday_proxy_review(
            portfolio_state=current_state,
            config_path=self.paths.intraday_proxy_config_path,
            realtime_path=self.paths.intraday_realtime_path,
        )

        self.assertEqual(review["status"], "available")
        by_code = {item["fund_code"]: item for item in review["funds"]}
        self.assertEqual(by_code["012734"]["proxy_method"], "holdings")
        self.assertGreater(len(by_code["012734"]["driver_breakdown"]), 1)
        self.assertEqual(by_code["011609"]["proxy_method"], "fallback_mapping")
        self.assertEqual(len(by_code["011609"]["driver_breakdown"]), 1)
        self.assertEqual(by_code["012734"]["data_quality"], "real")
        self.assertIsNotNone(by_code["012734"]["expected_close_band"])
        self.assertIsNotNone(by_code["012734"]["support_level"])
        self.assertIsNotNone(by_code["012734"]["resistance_level"])
        self.assertIn("support_resistance_basis", by_code["012734"]["evidence"])

    def test_intraday_sentiment_classification_outputs_evidence(self) -> None:
        panic = classify_intraday_sentiment(
            {
                "price_trend_pct": -2.6,
                "volume_ratio": 1.9,
                "amplitude_pct": 4.8,
                "drawdown_from_high_pct": -2.4,
            }
        )
        breakout = classify_intraday_sentiment(
            {
                "price_trend_pct": 2.1,
                "volume_ratio": 1.75,
                "amplitude_pct": 2.4,
                "drawdown_from_high_pct": -0.2,
            }
        )

        self.assertEqual(panic["label"], "intraday_panic_selloff")
        self.assertIn("matched_rules", panic["evidence"])
        self.assertIn("close_position_in_range", panic["evidence"])
        self.assertIn("breakout_distance_pct", panic["evidence"])
        self.assertIn("confidence_score", panic["evidence"])
        self.assertEqual(breakout["label"], "intraday_volume_breakout")
        self.assertIn("price_trend_pct", breakout["evidence"])

    def test_intraday_threshold_sanity_labels_are_distinguishable(self) -> None:
        config = load_portfolio_state(self.paths.portfolio_state_path)
        self.assertGreater(len(config.assets), 0)
        labels = run_intraday_sentiment_sanity()
        self.assertEqual(labels["panic"], "intraday_panic_selloff")
        self.assertEqual(labels["washout"], "intraday_distribution_or_washout")
        self.assertEqual(labels["chase"], "intraday_momentum_chase")
        self.assertEqual(labels["chop"], "intraday_range_chop")
        self.assertEqual(labels["drift_down"], "intraday_low_volume_drift_down")
        self.assertEqual(labels["rebound"], "intraday_low_volume_rebound")
        self.assertEqual(labels["breakout"], "intraday_volume_breakout")
        self.assertEqual(labels["stall"], "intraday_high_level_stall")

    def test_intraday_sentiment_boundary_scenarios_cover_all_8_classes(self) -> None:
        scenarios = {
            "intraday_momentum_chase": {"price_trend_pct": 1.25, "volume_ratio": 1.36, "amplitude_pct": 1.8, "drawdown_from_high_pct": -0.4},
            "intraday_panic_selloff": {"price_trend_pct": -2.05, "volume_ratio": 1.62, "amplitude_pct": 3.5, "drawdown_from_high_pct": -1.7},
            "intraday_distribution_or_washout": {"price_trend_pct": -0.5, "volume_ratio": 1.4, "amplitude_pct": 3.2, "drawdown_from_high_pct": -2.0},
            "intraday_range_chop": {"price_trend_pct": 0.35, "volume_ratio": 1.0, "amplitude_pct": 1.3, "drawdown_from_high_pct": -0.6},
            "intraday_low_volume_drift_down": {"price_trend_pct": -0.8, "volume_ratio": 0.85, "amplitude_pct": 1.2, "drawdown_from_high_pct": -1.0},
            "intraday_low_volume_rebound": {"price_trend_pct": 0.6, "volume_ratio": 0.92, "amplitude_pct": 1.6, "drawdown_from_high_pct": -0.3},
            "intraday_volume_breakout": {"price_trend_pct": 2.0, "volume_ratio": 1.7, "amplitude_pct": 2.2, "drawdown_from_high_pct": -0.2},
            "intraday_high_level_stall": {"price_trend_pct": 1.05, "volume_ratio": 1.05, "amplitude_pct": 1.4, "drawdown_from_high_pct": -1.0},
        }
        for expected_label, metrics in scenarios.items():
            with self.subTest(expected_label=expected_label):
                result = classify_intraday_sentiment(metrics)
                self.assertEqual(result["label"], expected_label)

    def test_intraday_sentiment_insufficient_evidence_goes_neutral_observe(self) -> None:
        result = classify_intraday_sentiment(
            {
                "price_trend_pct": 0.05,
                "volume_ratio": 1.02,
                "amplitude_pct": 0.3,
                "drawdown_from_high_pct": -0.05,
            }
        )
        self.assertEqual(result["label"], "intraday_neutral_observe")

    def test_intraday_proxy_review_covers_all_mapped_portfolio_funds(self) -> None:
        current_state = load_portfolio_state(self.paths.portfolio_state_path)
        review = build_intraday_proxy_review(
            portfolio_state=current_state,
            config_path=self.paths.intraday_proxy_config_path,
            realtime_path=self.paths.intraday_realtime_path,
        )
        mapped_symbols = {
            asset.symbol
            for asset in current_state.assets
            if asset.symbol in {"012734", "011609", "024620", "018028", "025833", "017193"}
        }
        reviewed_symbols = {item["fund_code"] for item in review["funds"]}
        self.assertSetEqual(mapped_symbols, reviewed_symbols)

    def test_intraday_real_fetcher_chain_falls_back_to_json_payload(self) -> None:
        providers = build_default_intraday_data_chain(self.paths)
        payload = refresh_intraday_proxy_inputs(providers[0], providers[1] if len(providers) > 1 else None)
        self.assertEqual(payload["status"], "success")
        self.assertIn("drivers", payload)
        self.assertGreater(len(payload["drivers"]), 0)

    def test_intraday_proxy_review_returns_structured_unavailable_when_realtime_missing(self) -> None:
        current_state = load_portfolio_state(self.paths.portfolio_state_path)
        missing_path = Path(self.tempdir.name) / "missing_intraday_realtime.json"

        review = build_intraday_proxy_review(
            portfolio_state=current_state,
            config_path=self.paths.intraday_proxy_config_path,
            realtime_path=missing_path,
        )

        self.assertEqual(review["status"], "unavailable")
        self.assertEqual(review["reason"], "realtime_feed_missing")
        self.assertTrue(all(item["status"] == "unavailable" for item in review["funds"]))
        self.assertTrue(all(item["proxy_nav_now"] is None for item in review["funds"]))

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

    def test_daily_review_workflow_persists_daily_report(self) -> None:
        self.repository.initialize()

        result = run_daily_review(self.paths, self.repository, news_limit=5)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["price_refresh"]["status"], "success")
        self.assertEqual(result["news_refresh"]["status"], "success")
        latest_report = self.repository.fetch_latest_report("daily")
        self.assertIsNotNone(latest_report)
        self.assertEqual(latest_report["report_type"], "daily")
        self.assertEqual(latest_report["content_json"]["schema_version"], "1.0")
        self.assertIn("action_items", latest_report["content_json"])
        self.assertIn("chart_artifacts", latest_report["content_json"])
        self.assertIn("intraday_market", latest_report["content_json"])
        section_ids = [item["section_id"] for item in latest_report["content_json"]["sections"]]
        self.assertIn("intraday_proxy_sentiment", section_ids)
        self.assertIn(latest_report["content_json"]["data_quality"], {"real", "fallback", "mixed"})
        self.assertIn("provider_notes", latest_report["content_json"])
        self.assertIn("data_quality", latest_report["content_json"]["summary"])
        self.assertEqual(result["intraday_market"]["status"], "available")
        self.assertNotIn("sentiment_label=", latest_report["content_md"])
        self.assertIn("结论=", latest_report["content_md"])
        self.assertIn("支撑位=", latest_report["content_md"])
        self.assertIn("压力/突破位=", latest_report["content_md"])

    def test_daily_chart_renderer_outputs_png_when_history_is_available(self) -> None:
        chart = render_daily_price_chart(
            paths=self.paths,
            report_time="2026-03-11 19:52:37",
            series=[
                {
                    "name": "示例基金",
                    "points": [
                        {"x": "03-06", "y": 1.01},
                        {"x": "03-07", "y": 1.02},
                        {"x": "03-10", "y": 1.03},
                    ],
                }
            ],
        )

        self.assertEqual(chart["status"], "success")
        self.assertIn("message", chart)
        self.assertTrue(Path(str(chart["path"])).exists())

    def test_daily_chart_renderer_skips_when_history_is_insufficient(self) -> None:
        chart = render_daily_price_chart(
            paths=self.paths,
            report_time="2026-03-11 19:52:37",
            series=[{"name": "示例基金", "points": [{"x": "03-10", "y": 1.03}]}],
        )

        self.assertEqual(chart["status"], "skipped")
        self.assertEqual(chart["reason"], "insufficient_history")

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

    @unittest.skipUnless(ocr_backend_available(), "rapidocr_onnxruntime is required for OCR tests")
    def test_parse_gold_snapshot_from_sample_image(self) -> None:
        if not self.gold_screenshot_path.exists():
            self.skipTest("gold screenshot fixture not present in /root/usrFile")

        parsed = parse_gold_snapshot(extract_ocr_lines(self.gold_screenshot_path))

        self.assertEqual(parsed["snapshot_type"], "gold_position")
        self.assertEqual(parsed["asset"]["category"], "gold")
        self.assertAlmostEqual(parsed["asset"]["shares"], 12.1713, places=4)
        self.assertAlmostEqual(parsed["asset"]["value"], 14077.33, places=2)
        self.assertAlmostEqual(parsed["asset"]["average_cost"], 1124.36, places=2)
        self.assertAlmostEqual(parsed["asset"]["profit"], 392.45, places=2)
        self.assertAlmostEqual(parsed["metrics"]["current_price"], 1156.60, places=2)

    @unittest.skipUnless(ocr_backend_available(), "rapidocr_onnxruntime is required for OCR tests")
    def test_parse_portfolio_snapshot_from_sample_image(self) -> None:
        if not self.portfolio_screenshot_path.exists():
            self.skipTest("portfolio screenshot fixture not present in /root/usrFile")

        parsed = parse_portfolio_snapshot(extract_ocr_lines(self.portfolio_screenshot_path))

        self.assertEqual(parsed["snapshot_type"], "portfolio_overview")
        self.assertAlmostEqual(parsed["summary"]["total_value"], 35805.93, places=2)
        self.assertAlmostEqual(parsed["summary"]["cash_value"], 9938.51, places=2)
        self.assertGreaterEqual(parsed["summary"]["holding_count"], 7)
        by_name = {item["name"]: item for item in parsed["holdings"]}
        self.assertAlmostEqual(by_name["天弘中证电网设备主题指数C"]["value"], 2364.57, places=2)
        self.assertAlmostEqual(by_name["广发中债7-10年期国开行债券指数E"]["value"], 7020.93, places=2)
        self.assertAlmostEqual(by_name["余额宝"]["value"], 9938.51, places=2)

    @unittest.skipUnless(ocr_backend_available(), "rapidocr_onnxruntime is required for OCR tests")
    def test_build_ocr_portfolio_import_merges_two_sample_images(self) -> None:
        if not self.gold_screenshot_path.exists() or not self.portfolio_screenshot_path.exists():
            self.skipTest("OCR screenshot fixtures not present in /root/usrFile")

        result = build_ocr_portfolio_import(
            portfolio_image_path=self.portfolio_screenshot_path,
            gold_image_path=self.gold_screenshot_path,
        )

        self.assertEqual(result["status"], "success")
        self.assertIsNotNone(result["portfolio_snapshot"])
        self.assertIsNotNone(result["gold_snapshot"])
        self.assertGreaterEqual(len(result["merged_portfolio"]["assets"]), 8)
        self.assertAlmostEqual(result["merged_portfolio"]["total_value"], 49883.26, places=2)
        self.assertIn("sync_to_portfolio_state_via_portfolio_editor", result["next_actions"])

    def test_snapshot_import_prefers_vision_client_when_available(self) -> None:
        class FakeVisionClient:
            def import_snapshot(self, portfolio_image_path: Path | None = None, gold_image_path: Path | None = None) -> dict[str, object]:
                return {
                    "status": "success",
                    "source": "vision-model",
                    "portfolio_snapshot": {"summary": {"total_value": 123.45}},
                    "gold_snapshot": None,
                    "merged_portfolio": {"updated_at": "", "assets": [], "total_value": 123.45},
                    "next_actions": ["sync_to_portfolio_state_via_portfolio_editor"],
                }

        result = build_snapshot_import(
            portfolio_image_path=self.portfolio_screenshot_path,
            gold_image_path=self.gold_screenshot_path,
            vision_client=FakeVisionClient(),
        )

        self.assertEqual(result["source"], "vision-model")
        self.assertFalse(result["fallback_used"])
        self.assertAlmostEqual(result["merged_portfolio"]["total_value"], 123.45, places=2)

    @unittest.skipUnless(ocr_backend_available(), "rapidocr_onnxruntime is required for OCR fallback tests")
    def test_snapshot_import_falls_back_to_ocr_when_vision_client_fails(self) -> None:
        if not self.gold_screenshot_path.exists() or not self.portfolio_screenshot_path.exists():
            self.skipTest("OCR screenshot fixtures not present in /root/usrFile")

        class FailingVisionClient:
            def import_snapshot(self, portfolio_image_path: Path | None = None, gold_image_path: Path | None = None) -> dict[str, object]:
                raise RuntimeError("vision parser timeout")

        result = build_snapshot_import(
            portfolio_image_path=self.portfolio_screenshot_path,
            gold_image_path=self.gold_screenshot_path,
            vision_client=FailingVisionClient(),
        )

        self.assertEqual(result["source"], "ocr-fallback")
        self.assertTrue(result["fallback_used"])
        self.assertIn("vision parser timeout", result["fallback_reason"])
        self.assertAlmostEqual(result["merged_portfolio"]["total_value"], 49883.26, places=2)


if __name__ == "__main__":
    unittest.main()
