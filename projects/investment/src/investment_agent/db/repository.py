from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from pathlib import Path
from typing import Any

from investment_agent.models.portfolio import PortfolioState
from investment_agent.providers.market_data import MarketQuote
from investment_agent.providers.news_data import NewsItem


def _normalize_text(value: Any) -> str:
    normalized = re.sub(r"\s+", " ", str(value or "").strip().lower())
    return normalized


def _canonicalize_json(value: Any) -> str:
    if value is None:
        return ""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _derive_asset_code(signal_type: str, evidence: dict[str, Any]) -> str:
    breach = evidence.get("breach") if isinstance(evidence, dict) else None
    if isinstance(breach, dict) and breach.get("category"):
        return _normalize_text(breach["category"])
    for key in ("asset_code", "symbol", "asset", "theme", "category"):
        value = evidence.get(key) if isinstance(evidence, dict) else None
        if value:
            return _normalize_text(value)
    return _normalize_text(signal_type) or "unknown"


class InvestmentRepository:
    def __init__(self, db_path: Path, schema_path: Path) -> None:
        self.db_path = Path(db_path)
        self.schema_path = Path(schema_path)

    def initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as connection:
            connection.executescript(self.schema_path.read_text(encoding="utf-8"))
            self._apply_schema_migrations(connection)
            connection.commit()

    def _apply_schema_migrations(self, connection: sqlite3.Connection) -> None:
        columns = {
            str(row[1])
            for row in connection.execute("PRAGMA table_info(risk_signals)").fetchall()
        }
        if "dedupe_key" not in columns:
            connection.execute("ALTER TABLE risk_signals ADD COLUMN dedupe_key TEXT")

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_risk_signals_status_type_date
            ON risk_signals(status, signal_type, signal_time)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_risk_signals_dedupe_open
            ON risk_signals(status, dedupe_key, signal_time)
            """
        )

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

    def fetch_recent_price_history(self, asset_code: str, limit: int = 30) -> list[dict[str, Any]]:
        with sqlite3.connect(self.db_path) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                """
                SELECT asset_code, source, trade_date, close_price, high_price, low_price, volume, fetched_at
                FROM price_snapshots
                WHERE asset_code = ?
                ORDER BY trade_date DESC, fetched_at DESC
                LIMIT ?
                """,
                (asset_code, limit),
            ).fetchall()
        deduped_by_trade_date: dict[str, dict[str, Any]] = {}
        for row in rows:
            item = dict(row)
            trade_date = str(item["trade_date"])
            if trade_date not in deduped_by_trade_date:
                deduped_by_trade_date[trade_date] = item
        items = list(deduped_by_trade_date.values())
        items.reverse()
        return items

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

    def _build_risk_signal_dedupe_key(
        self,
        signal_time: str,
        signal_type: str,
        severity: str,
        message: str,
        evidence: dict[str, Any],
    ) -> str:
        signal_date = str(signal_time).split(" ", 1)[0]
        asset_code = _derive_asset_code(signal_type, evidence)
        normalized_evidence = _canonicalize_json(evidence)
        evidence_hash = hashlib.sha1(normalized_evidence.encode("utf-8")).hexdigest()[:16]
        parts = [
            signal_date,
            _normalize_text(signal_type),
            asset_code,
            _normalize_text(severity),
            evidence_hash,
        ]
        return "|".join(parts)

    def store_risk_signal(
        self,
        signal_time: str,
        signal_type: str,
        severity: str,
        message: str,
        evidence: dict[str, Any],
        status: str = "open",
    ) -> int:
        dedupe_key = self._build_risk_signal_dedupe_key(
            signal_time=signal_time,
            signal_type=signal_type,
            severity=severity,
            message=message,
            evidence=evidence,
        )
        with sqlite3.connect(self.db_path) as connection:
            connection.row_factory = sqlite3.Row
            existing = connection.execute(
                """
                SELECT id
                FROM risk_signals
                WHERE date(signal_time) = date(?)
                  AND signal_type = ?
                  AND status = ?
                  AND (
                        dedupe_key = ?
                     OR (
                        severity = ?
                        AND message = ?
                     )
                  )
                ORDER BY id DESC
                LIMIT 1
                """,
                (signal_time, signal_type, status, dedupe_key, severity, message),
            ).fetchone()
            if existing is not None:
                connection.execute(
                    """
                    UPDATE risk_signals
                    SET signal_time = ?, severity = ?, message = ?, evidence_json = ?, dedupe_key = ?
                    WHERE id = ?
                    """,
                    (
                        signal_time,
                        severity,
                        message,
                        _canonicalize_json(evidence),
                        dedupe_key,
                        int(existing["id"]),
                    ),
                )
                connection.commit()
                return int(existing["id"])

            cursor = connection.execute(
                """
                INSERT INTO risk_signals (
                    signal_time, signal_type, severity, message, evidence_json, dedupe_key, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    signal_time,
                    signal_type,
                    severity,
                    message,
                    _canonicalize_json(evidence),
                    dedupe_key,
                    status,
                ),
            )
            connection.commit()
        return int(cursor.lastrowid)

    def close_open_risk_signals(
        self,
        signal_types: list[str],
        active_messages_by_type: dict[str, set[str]],
        signal_date: str | None = None,
        active_dedupe_keys_by_type: dict[str, set[str]] | None = None,
    ) -> int:
        if not signal_types:
            return 0
        closed = 0
        with sqlite3.connect(self.db_path) as connection:
            connection.row_factory = sqlite3.Row
            placeholders = ", ".join("?" for _ in signal_types)
            query = f"""
                SELECT id, signal_type, message, dedupe_key
                FROM risk_signals
                WHERE status = 'open' AND signal_type IN ({placeholders})
                """
            parameters: tuple[Any, ...] = tuple(signal_types)
            if signal_date is not None:
                query += " AND date(signal_time) = date(?)"
                parameters = (*parameters, signal_date)

            rows = connection.execute(query, parameters).fetchall()
            dedupe_map = active_dedupe_keys_by_type or {}
            for row in rows:
                signal_type = str(row["signal_type"])
                message = str(row["message"])
                dedupe_key = str(row["dedupe_key"] or "")
                if dedupe_key and dedupe_key in dedupe_map.get(signal_type, set()):
                    continue
                if message in active_messages_by_type.get(signal_type, set()):
                    continue
                connection.execute(
                    """
                    UPDATE risk_signals
                    SET status = 'closed'
                    WHERE id = ?
                    """,
                    (int(row["id"]),),
                )
                closed += 1
            connection.commit()
        return closed

    def store_investment_suggestion(
        self,
        suggestion_time: str,
        suggestion_type: str,
        content: dict[str, Any],
        rationale: str,
        status: str = "draft",
    ) -> int:
        with sqlite3.connect(self.db_path) as connection:
            connection.row_factory = sqlite3.Row
            existing = connection.execute(
                """
                SELECT id
                FROM investment_suggestions
                WHERE date(suggestion_time) = date(?) AND suggestion_type = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (suggestion_time, suggestion_type),
            ).fetchone()
            if existing is not None:
                connection.execute(
                    """
                    UPDATE investment_suggestions
                    SET suggestion_time = ?, content_json = ?, rationale = ?, status = ?
                    WHERE id = ?
                    """,
                    (
                        suggestion_time,
                        json.dumps(content, ensure_ascii=False, sort_keys=True),
                        rationale,
                        status,
                        int(existing["id"]),
                    ),
                )
                connection.commit()
                return int(existing["id"])

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
            connection.row_factory = sqlite3.Row
            existing = connection.execute(
                """
                SELECT id
                FROM reports
                WHERE date(report_time) = date(?) AND report_type = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (report_time, report_type),
            ).fetchone()
            if existing is not None:
                connection.execute(
                    """
                    UPDATE reports
                    SET report_time = ?, title = ?, content_md = ?, content_json = ?
                    WHERE id = ?
                    """,
                    (
                        report_time,
                        title,
                        content_md,
                        json.dumps(content_json, ensure_ascii=False, sort_keys=True),
                        int(existing["id"]),
                    ),
                )
                connection.commit()
                return int(existing["id"])

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

    def cleanup_legacy_same_day_duplicates(self, dry_run: bool = True) -> dict[str, int]:
        statements = {
            "risk_signals": """
                DELETE FROM risk_signals
                WHERE id IN (
                    SELECT t.id
                    FROM risk_signals t
                    JOIN (
                        SELECT date(signal_time) AS signal_date, signal_type, status, MAX(id) AS keep_id
                        FROM risk_signals
                        GROUP BY date(signal_time), signal_type, status
                        HAVING COUNT(*) > 1
                    ) d
                      ON date(t.signal_time) = d.signal_date
                     AND t.signal_type = d.signal_type
                     AND t.status = d.status
                    WHERE t.id <> d.keep_id
                )
            """,
            "investment_suggestions": """
                DELETE FROM investment_suggestions
                WHERE id IN (
                    SELECT t.id
                    FROM investment_suggestions t
                    JOIN (
                        SELECT date(suggestion_time) AS suggestion_date, suggestion_type, MAX(id) AS keep_id
                        FROM investment_suggestions
                        GROUP BY date(suggestion_time), suggestion_type
                        HAVING COUNT(*) > 1
                    ) d
                      ON date(t.suggestion_time) = d.suggestion_date
                     AND t.suggestion_type = d.suggestion_type
                    WHERE t.id <> d.keep_id
                )
            """,
            "reports": """
                DELETE FROM reports
                WHERE id IN (
                    SELECT t.id
                    FROM reports t
                    JOIN (
                        SELECT date(report_time) AS report_date, report_type, MAX(id) AS keep_id
                        FROM reports
                        GROUP BY date(report_time), report_type
                        HAVING COUNT(*) > 1
                    ) d
                      ON date(t.report_time) = d.report_date
                     AND t.report_type = d.report_type
                    WHERE t.id <> d.keep_id
                )
            """,
        }

        deleted_counts = {"risk_signals": 0, "investment_suggestions": 0, "reports": 0}
        with sqlite3.connect(self.db_path) as connection:
            self._apply_schema_migrations(connection)
            for table_name, sql in statements.items():
                cursor = connection.execute(sql)
                deleted_counts[table_name] = int(cursor.rowcount or 0)
            if dry_run:
                connection.rollback()
            else:
                connection.commit()
        deleted_counts["total_deleted"] = sum(deleted_counts.values())
        deleted_counts["dry_run"] = 1 if dry_run else 0
        return deleted_counts

    def count_rows(self, table_name: str) -> int:
        with sqlite3.connect(self.db_path) as connection:
            row = connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
        return int(row[0])

    def dump_snapshot_json(self) -> str:
        latest = self.fetch_latest_snapshot()
        return json.dumps(latest, ensure_ascii=False, sort_keys=True)
