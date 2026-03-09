from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from investment_agent.models.portfolio import PortfolioState
from investment_agent.providers.market_data import MarketQuote


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
                        None,
                        asset.value,
                        asset.value - asset.profit if asset.profit is not None else None,
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

    def count_rows(self, table_name: str) -> int:
        with sqlite3.connect(self.db_path) as connection:
            row = connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
        return int(row[0])

    def dump_snapshot_json(self) -> str:
        latest = self.fetch_latest_snapshot()
        return json.dumps(latest, ensure_ascii=False, sort_keys=True)
