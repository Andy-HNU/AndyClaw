from __future__ import annotations

import base64
import importlib.util
import json
import os
from pathlib import Path
from typing import Any, Protocol

from investment_agent.services.ocr_importer import build_ocr_portfolio_import


class SnapshotImporterError(RuntimeError):
    pass


class SnapshotVisionClient(Protocol):
    def import_snapshot(
        self, portfolio_image_path: Path | None = None, gold_image_path: Path | None = None
    ) -> dict[str, Any]:
        ...


def openai_vision_available() -> bool:
    return bool(os.getenv("OPENAI_API_KEY")) and importlib.util.find_spec("openai") is not None


class OpenAIVisionSnapshotClient:
    def __init__(self, model: str = "gpt-4.1-mini") -> None:
        self.model = model

    def import_snapshot(
        self, portfolio_image_path: Path | None = None, gold_image_path: Path | None = None
    ) -> dict[str, Any]:
        if not openai_vision_available():
            raise SnapshotImporterError("OpenAI vision client is not configured in the current environment")

        from openai import OpenAI

        client = OpenAI()
        prompt = self._build_prompt()
        content: list[dict[str, Any]] = [{"type": "input_text", "text": prompt}]
        if portfolio_image_path is not None:
            content.append(
                {
                    "type": "input_image",
                    "image_url": self._image_data_url(portfolio_image_path),
                }
            )
        if gold_image_path is not None:
            content.append(
                {
                    "type": "input_image",
                    "image_url": self._image_data_url(gold_image_path),
                }
            )

        response = client.responses.create(
            model=self.model,
            input=[{"role": "user", "content": content}],
        )
        payload = json.loads(response.output_text)
        payload["status"] = payload.get("status", "success")
        payload["source"] = "vision-model"
        return payload

    def _image_data_url(self, path: Path) -> str:
        mime_type = "image/jpeg" if path.suffix.lower() in {".jpg", ".jpeg"} else "image/png"
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        return f"data:{mime_type};base64,{encoded}"

    def _build_prompt(self) -> str:
        schema = {
            "status": "success",
            "portfolio_snapshot": {
                "snapshot_type": "portfolio_overview",
                "summary": {
                    "total_value": 0.0,
                    "cash_value": 0.0,
                    "captured_at": "",
                    "holding_count": 0,
                },
                "holdings": [
                    {
                        "name": "",
                        "category": "stock|bond|gold|cash",
                        "asset_type": "bond_fund|etf|index_fund|thematic_fund|commodity|cash|unknown",
                        "symbol": "",
                        "theme": "",
                        "value": 0.0,
                        "shares": None,
                        "average_cost": None,
                        "profit": None,
                        "profit_rate": None,
                        "day_profit": None,
                        "cumulative_profit": None,
                        "allocation_pct": None,
                    }
                ],
                "missing_fields": {},
                "confidence_notes": [],
            },
            "gold_snapshot": {
                "snapshot_type": "gold_position",
                "asset": {
                    "name": "黄金",
                    "category": "gold",
                    "asset_type": "commodity",
                    "symbol": "Au99.99",
                    "value": 0.0,
                    "shares": 0.0,
                    "average_cost": 0.0,
                    "profit": 0.0,
                    "profit_rate": 0.0,
                },
                "metrics": {
                    "total_value": 0.0,
                    "sell_fee": 0.0,
                    "holding_profit": 0.0,
                    "cumulative_profit": 0.0,
                    "current_price": 0.0,
                    "price_change": 0.0,
                    "price_change_pct": 0.0,
                    "captured_at": "",
                },
                "missing_fields": [],
                "confidence_notes": [],
            },
            "merged_portfolio": {"updated_at": "", "assets": [], "total_value": 0.0},
            "next_actions": [],
        }
        return (
            "Parse the attached Chinese investment screenshots into strict JSON only. "
            "Do not include markdown. Use null for unknown values. "
            "Recognize holdings, cash, and a separate gold position page if present. "
            "Preserve asset names exactly as shown. "
            "Return JSON matching this schema: "
            f"{json.dumps(schema, ensure_ascii=False)}"
        )


def build_snapshot_import(
    portfolio_image_path: Path | None = None,
    gold_image_path: Path | None = None,
    vision_client: SnapshotVisionClient | None = None,
) -> dict[str, Any]:
    if vision_client is not None:
        try:
            result = vision_client.import_snapshot(portfolio_image_path, gold_image_path)
            result["source"] = result.get("source", "vision-model")
            result["fallback_used"] = False
            return result
        except Exception as exc:
            fallback = build_ocr_portfolio_import(portfolio_image_path, gold_image_path)
            fallback["source"] = "ocr-fallback"
            fallback["fallback_used"] = True
            fallback["fallback_reason"] = str(exc)
            return fallback

    if openai_vision_available():
        try:
            result = OpenAIVisionSnapshotClient().import_snapshot(portfolio_image_path, gold_image_path)
            result["source"] = result.get("source", "vision-model")
            result["fallback_used"] = False
            return result
        except Exception as exc:
            fallback = build_ocr_portfolio_import(portfolio_image_path, gold_image_path)
            fallback["source"] = "ocr-fallback"
            fallback["fallback_used"] = True
            fallback["fallback_reason"] = str(exc)
            return fallback

    fallback = build_ocr_portfolio_import(portfolio_image_path, gold_image_path)
    fallback["source"] = "ocr-fallback"
    fallback["fallback_used"] = True
    fallback["fallback_reason"] = "vision client unavailable"
    return fallback
