from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from investment_agent.models.portfolio import PortfolioState


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

    def count_rows(self, table_name: str) -> int:
        with sqlite3.connect(self.db_path) as connection:
            row = connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
        return int(row[0])

    def dump_snapshot_json(self) -> str:
        latest = self.fetch_latest_snapshot()
        return json.dumps(latest, ensure_ascii=False, sort_keys=True)
