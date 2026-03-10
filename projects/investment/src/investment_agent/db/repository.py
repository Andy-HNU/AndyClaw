from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from investment_agent.models.portfolio import PortfolioState
from investment_agent.providers.market_data import MarketQuote
from investment_agent.providers.news_data import NewsItem


class InvestmentRepository:
    def __init__(self, db_path: Path, schema_path: Path) -> None:
        self.db_path = Path(db_path)
        self.schema_path = Path(schema_path)

    def initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as connection:
            connection.executescript(self.schema_path.read_text(encoding="utf-8"))
            connection.commit()

    def seed_portfolio_state(self, state: PortfolioState) -> None:
        grouped = state.grouped_values()
        with sqlite3.connect(self.db_path) as connection:
            connection.execute("DELETE FROM portfolio_assets")
            connection.execute("DELETE FROM portfolio_snapshots")
            for asset in state.assets:
                connection.execute(
                    """
                    INSERT INTO portfolio_assets (
                        asset_code, asset_name, category, subcategory,
                        quantity, market_value, cost_basis, currency, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        asset.theme or asset.name,
                        asset.name,
                        asset.category,
                        asset.theme,
                        asset.shares,
                        asset.value,
                        (
                            round(asset.average_cost * asset.shares, 2)
                            if asset.average_cost is not None and asset.shares is not None
                            else (asset.value - asset.profit if asset.profit is not None else None)
                        ),
                        "CNY",
                        state.updated_at,
                    ),
                )

            connection.execute(
                """
                INSERT INTO portfolio_snapshots (
                    snapshot_time, total_value, stock_value, bond_value,
                    gold_value, cash_value, note
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    state.updated_at,
                    state.total_value,
                    grouped.get("stock"),
                    grouped.get("bond"),
                    grouped.get("gold"),
                    grouped.get("cash"),
                    "seeded from portfolio_state.json",
                ),
            )
            connection.commit()

    def fetch_latest_snapshot(self) -> dict[str, Any] | None:
        with sqlite3.connect(self.db_path) as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(
                """
                SELECT snapshot_time, total_value, stock_value, bond_value, gold_value, cash_value, note
                FROM portfolio_snapshots
                ORDER BY snapshot_time DESC
                LIMIT 1
                """
            ).fetchone()
        return dict(row) if row else None

    def fetch_portfolio_assets(self) -> list[dict[str, Any]]:
        with sqlite3.connect(self.db_path) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                """
                SELECT asset_code, asset_name, category, subcategory, quantity, market_value, cost_basis, currency, updated_at
                FROM portfolio_assets
                ORDER BY id ASC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def store_price_snapshots(self, quotes: list[MarketQuote]) -> int:
        with sqlite3.connect(self.db_path) as connection:
            for quote in quotes:
                connection.execute(
                    """
                    INSERT INTO price_snapshots (
                        asset_code, source, trade_date, close_price,
                        high_price, low_price, volume, fetched_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        quote.asset_code,
                        quote.source,
                        quote.trade_date,
                        quote.close_price,
                        quote.high_price,
                        quote.low_price,
                        quote.volume,
                        quote.fetched_at,
                    ),
                )
            connection.commit()
        return len(quotes)

    def fetch_latest_price_snapshot(self, asset_code: str) -> dict[str, Any] | None:
        with sqlite3.connect(self.db_path) as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(
                """
                SELECT asset_code, source, trade_date, close_price, high_price, low_price, volume, fetched_at
                FROM price_snapshots
                WHERE asset_code = ?
                ORDER BY trade_date DESC, fetched_at DESC
                LIMIT 1
                """,
                (asset_code,),
            ).fetchone()
        return dict(row) if row else None

    def store_news_items(self, news_items: list[NewsItem]) -> int:
        with sqlite3.connect(self.db_path) as connection:
            for item in news_items:
                connection.execute(
                    """
                    INSERT INTO news_items (
                        source, title, summary, url, published_at, topic, sentiment_hint, fetched_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item.source,
                        item.title,
                        item.summary,
                        item.url,
                        item.published_at,
                        item.topic,
                        item.sentiment_hint,
                        item.fetched_at,
                    ),
                )
            connection.commit()
        return len(news_items)

    def fetch_recent_news(self, limit: int = 5) -> list[dict[str, Any]]:
        with sqlite3.connect(self.db_path) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                """
                SELECT source, title, summary, url, published_at, topic, sentiment_hint, fetched_at
                FROM news_items
                ORDER BY published_at DESC, id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def store_analysis_result(self, analysis: dict[str, Any], status: str = "fresh") -> int:
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO analysis_results (
                    analysis_time, total_value, allocation_json, deviation_json, status
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    analysis["updated_at"],
                    analysis["total_value"],
                    json.dumps(analysis["allocations_pct"], ensure_ascii=False, sort_keys=True),
                    json.dumps(analysis["deviations_pct"], ensure_ascii=False, sort_keys=True),
                    status,
                ),
            )
            connection.commit()
        return int(cursor.lastrowid)

    def fetch_latest_analysis(self) -> dict[str, Any] | None:
        with sqlite3.connect(self.db_path) as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(
                """
                SELECT analysis_time, total_value, allocation_json, deviation_json, status
                FROM analysis_results
                ORDER BY id DESC
                LIMIT 1
                """
            ).fetchone()
        if row is None:
            return None
        result = dict(row)
        result["allocation_json"] = json.loads(result["allocation_json"])
        result["deviation_json"] = json.loads(result["deviation_json"])
        return result

    def store_risk_signal(
        self,
        signal_time: str,
        signal_type: str,
        severity: str,
        message: str,
        evidence: dict[str, Any],
        status: str = "open",
    ) -> int:
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO risk_signals (
                    signal_time, signal_type, severity, message, evidence_json, status
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    signal_time,
                    signal_type,
                    severity,
                    message,
                    json.dumps(evidence, ensure_ascii=False, sort_keys=True),
                    status,
                ),
            )
            connection.commit()
        return int(cursor.lastrowid)

    def store_investment_suggestion(
        self,
        suggestion_time: str,
        suggestion_type: str,
        content: dict[str, Any],
        rationale: str,
        status: str = "draft",
    ) -> int:
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO investment_suggestions (
                    suggestion_time, suggestion_type, content_json, rationale, status
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    suggestion_time,
                    suggestion_type,
                    json.dumps(content, ensure_ascii=False, sort_keys=True),
                    rationale,
                    status,
                ),
            )
            connection.commit()
        return int(cursor.lastrowid)

    def fetch_latest_investment_suggestion(self) -> dict[str, Any] | None:
        with sqlite3.connect(self.db_path) as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(
                """
                SELECT suggestion_time, suggestion_type, content_json, rationale, status
                FROM investment_suggestions
                ORDER BY id DESC
                LIMIT 1
                """
            ).fetchone()
        if row is None:
            return None
        result = dict(row)
        result["content_json"] = json.loads(result["content_json"])
        return result

    def fetch_open_risk_signals(self) -> list[dict[str, Any]]:
        with sqlite3.connect(self.db_path) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                """
                SELECT signal_time, signal_type, severity, message, evidence_json, status
                FROM risk_signals
                WHERE status = 'open'
                ORDER BY id ASC
                """
            ).fetchall()
        results: list[dict[str, Any]] = []
        for row in rows:
            item = dict(row)
            item["evidence_json"] = json.loads(item["evidence_json"])
            results.append(item)
        return results

    def fetch_risk_signals_by_ids(self, signal_ids: list[int]) -> list[dict[str, Any]]:
        if not signal_ids:
            return []
        placeholders = ", ".join("?" for _ in signal_ids)
        with sqlite3.connect(self.db_path) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                f"""
                SELECT id, signal_time, signal_type, severity, message, evidence_json, status
                FROM risk_signals
                WHERE id IN ({placeholders})
                ORDER BY id ASC
                """,
                tuple(signal_ids),
            ).fetchall()
        results: list[dict[str, Any]] = []
        for row in rows:
            item = dict(row)
            item["evidence_json"] = json.loads(item["evidence_json"])
            results.append(item)
        return results

    def store_report(
        self,
        report_time: str,
        report_type: str,
        title: str,
        content_md: str,
        content_json: dict[str, Any],
    ) -> int:
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO reports (
                    report_time, report_type, title, content_md, content_json
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    report_time,
                    report_type,
                    title,
                    content_md,
                    json.dumps(content_json, ensure_ascii=False, sort_keys=True),
                ),
            )
            connection.commit()
        return int(cursor.lastrowid)

    def fetch_latest_report(self, report_type: str | None = None) -> dict[str, Any] | None:
        query = """
            SELECT report_time, report_type, title, content_md, content_json
            FROM reports
        """
        parameters: tuple[Any, ...] = ()
        if report_type is not None:
            query += " WHERE report_type = ?"
            parameters = (report_type,)
        query += " ORDER BY id DESC LIMIT 1"

        with sqlite3.connect(self.db_path) as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(query, parameters).fetchone()
        if row is None:
            return None
        result = dict(row)
        result["content_json"] = json.loads(result["content_json"]) if result["content_json"] else None
        return result

    def count_rows(self, table_name: str) -> int:
        with sqlite3.connect(self.db_path) as connection:
            row = connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
        return int(row[0])

    def dump_snapshot_json(self) -> str:
        latest = self.fetch_latest_snapshot()
        return json.dumps(latest, ensure_ascii=False, sort_keys=True)
