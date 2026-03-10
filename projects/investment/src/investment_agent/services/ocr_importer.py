from __future__ import annotations

import importlib.util
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class OcrImporterError(RuntimeError):
    pass


@dataclass(frozen=True)
class OcrLine:
    text: str
    confidence: float


def ocr_backend_available() -> bool:
    return importlib.util.find_spec("rapidocr_onnxruntime") is not None


def _require_ocr_backend() -> None:
    if not ocr_backend_available():
        raise OcrImporterError(
            "rapidocr_onnxruntime is not installed; install it before using OCR import"
        )


def _clean_text(text: str) -> str:
    normalized = text.replace("~", "").replace(" ", "")
    normalized = normalized.replace("（", "(").replace("）", ")")
    normalized = normalized.replace("：", ":")
    return normalized.strip()


def extract_ocr_lines(image_path: Path) -> list[OcrLine]:
    _require_ocr_backend()
    from rapidocr_onnxruntime import RapidOCR

    engine = RapidOCR()
    result, _ = engine(str(image_path))
    lines: list[OcrLine] = []
    for item in result or []:
        text = _clean_text(str(item[1]))
        if not text:
            continue
        lines.append(OcrLine(text=text, confidence=float(item[2])))
    return lines


def _parse_float(token: str) -> float | None:
    match = re.search(r"[+-]?\d[\d,\.]*", token)
    if not match:
        return None
    raw = match.group(0)
    sign = ""
    if raw.startswith(("+", "-")):
        sign = raw[0]
        raw = raw[1:]
    raw = raw.replace(",", "")
    if raw.count(".") > 1:
        parts = raw.split(".")
        raw = "".join(parts[:-1]) + "." + parts[-1]
    normalized = f"{sign}{raw}"
    try:
        return float(normalized)
    except ValueError:
        return None


def _parse_signed_percent(token: str) -> float | None:
    match = re.search(r"([+-]?\d+(?:\.\d+)?)%", token)
    if not match:
        return None
    return float(match.group(1))


def _parse_first_labeled_value(lines: list[str], label: str) -> float | None:
    for line in lines:
        if label in line:
            value = _parse_float(line.split(label, 1)[-1])
            if value is not None:
                return value
    for index, line in enumerate(lines):
        if label in line and index + 1 < len(lines):
            value = _parse_float(lines[index + 1])
            if value is not None:
                return value
    return None


def _parse_timestamp(lines: list[str]) -> str | None:
    for line in lines:
        match = re.search(r"(20\d{2}-\d{2}-\d{2})?(\d{2}:\d{2}:\d{2})", line)
        if match:
            date_part = match.group(1) or ""
            time_part = match.group(2)
            return f"{date_part} {time_part}".strip()
    return None


def _parse_next_numeric(lines: list[str], start_index: int, window: int = 4) -> float | None:
    upper_bound = min(len(lines), start_index + 1 + window)
    for index in range(start_index + 1, upper_bound):
        value = _parse_float(lines[index])
        if value is not None:
            return value
    return None


def parse_gold_snapshot(lines: list[OcrLine]) -> dict[str, Any]:
    texts = [item.text for item in lines]
    shares = None
    for index, line in enumerate(texts):
        if "持仓克重" in line:
            shares = _parse_next_numeric(texts, index, window=4)
            if shares is not None:
                break
    total_value = None
    fee = None
    average_cost = None
    holding_profit = None
    cumulative_profit = None
    cost_index = None
    holding_index = None
    cumulative_index = None
    for index, line in enumerate(texts):
        if "当前总价值" in line:
            number_tokens = re.findall(r"[+-]?\d[\d,\.]*", line)
            parsed_values = [_parse_float(token) for token in number_tokens]
            parsed_values = [item for item in parsed_values if item is not None]
            if parsed_values:
                total_value = parsed_values[0]
            if len(parsed_values) >= 2:
                fee = parsed_values[1]
        if "成本均价" in line:
            cost_index = index
        if "持仓收益" in line:
            holding_index = index
        if "累计收益" in line:
            cumulative_index = index

    if None not in (cost_index, holding_index, cumulative_index):
        metrics_start = min(cost_index, holding_index, cumulative_index)
        metrics_end = max(cost_index, holding_index, cumulative_index)
        trailing_values: list[float] = []
        for line in texts[metrics_end + 1 :]:
            value = _parse_float(line)
            if value is not None:
                trailing_values.append(value)
            if len(trailing_values) >= 3:
                break
        if len(trailing_values) >= 3:
            average_cost, holding_profit, cumulative_profit = trailing_values[:3]

    if average_cost is None:
        average_cost = _parse_next_numeric(texts, cost_index or 0, window=6)
    if holding_profit is None:
        holding_profit = _parse_next_numeric(texts, holding_index or 0, window=6)
    if cumulative_profit is None:
        cumulative_profit = _parse_next_numeric(texts, cumulative_index or 0, window=6)

    current_price = None
    price_change = None
    price_change_pct = None
    for line in texts:
        if "实时金价" in line:
            continue
        if re.search(r"\d+\.\d+[+-]\d+\.\d+[+-]\d+\.\d+%", line):
            matches = re.findall(r"[+-]?\d+(?:\.\d+)?%?", line)
            if len(matches) >= 3:
                current_price = float(matches[0])
                price_change = float(matches[1])
                price_change_pct = float(matches[2].replace("%", ""))
                break
    return {
        "snapshot_type": "gold_position",
        "asset": {
            "name": "黄金",
            "category": "gold",
            "asset_type": "commodity",
            "symbol": "Au99.99",
            "value": total_value,
            "shares": shares,
            "average_cost": average_cost,
            "profit": holding_profit,
            "profit_rate": round((holding_profit / total_value) * 100, 4)
            if holding_profit is not None and total_value
            else None,
        },
        "metrics": {
            "total_value": total_value,
            "sell_fee": fee,
            "holding_profit": holding_profit,
            "cumulative_profit": cumulative_profit,
            "current_price": current_price,
            "price_change": price_change,
            "price_change_pct": price_change_pct,
            "captured_at": _parse_timestamp(texts),
        },
        "missing_fields": [
            key
            for key, value in {
                "value": total_value,
                "shares": shares,
                "average_cost": average_cost,
            }.items()
            if value is None
        ],
        "ocr_lines": texts,
    }


def _is_asset_name(line: str) -> bool:
    if line in {"基金", "基金稳健理财", "基金进阶理财"}:
        return False
    if any(token in line for token in ("基金", "ETF", "联接", "债券", "指数", "余额宝")):
        return not any(
            noise in line
            for noise in (
                "基金定投",
                "金选指数基金",
                "稳健理财",
                "进阶理财",
                "持有收益排序",
                "名称/金额",
                "全部持有",
                "收益明细",
                "交易记录",
                "近一周跌幅",
                "看看收益",
                "分析再做决定",
                "以上按照持有收益排序",
            )
        )
    return False


def _classify_holding_fields(block: list[str]) -> dict[str, Any]:
    amount = None
    day_profit = None
    holding_profit = None
    cumulative_profit = None
    allocation_pct = None
    profit_rate = None

    numeric_tokens = [token for token in block if re.search(r"[+-]?\d[\d,]*\.?\d*", token)]
    values: list[float] = []
    for token in numeric_tokens:
        percent = _parse_signed_percent(token)
        if percent is not None and "占比" not in token:
            profit_rate = percent
            continue
        if "占比" in token:
            allocation_pct = percent
            continue
        value = _parse_float(token)
        if value is not None:
            values.append(value)

    if values:
        amount = values[0]
    if len(values) >= 2:
        day_profit = values[1]
    if len(values) >= 3:
        holding_profit = values[2]
    if len(values) >= 4:
        cumulative_profit = values[3]
    elif holding_profit is not None:
        cumulative_profit = holding_profit

    return {
        "value": amount,
        "day_profit": day_profit,
        "profit": holding_profit,
        "cumulative_profit": cumulative_profit,
        "allocation_pct": allocation_pct,
        "profit_rate": profit_rate,
        "shares": None,
        "average_cost": None,
    }


def _infer_category(name: str) -> str:
    if "债" in name:
        return "bond"
    if "余额宝" in name or "现金" in name:
        return "cash"
    return "stock"


def _infer_asset_type(name: str) -> str:
    if "余额宝" in name or "现金" in name:
        return "cash"
    if "债" in name:
        return "bond_fund"
    if "ETF" in name and "联接" not in name:
        return "etf"
    if "联接" in name or "指数" in name:
        return "thematic_fund"
    return "thematic_fund"


def _infer_theme(name: str) -> str | None:
    mapping = {
        "电网": "power_grid",
        "高端装备": "advanced_manufacturing",
        "有色金属": "metals",
        "科创50": "broad_index",
        "人工智能": "ai",
        "机器人": "robotics",
    }
    for keyword, theme in mapping.items():
        if keyword in name:
            return theme
    return None


def _infer_symbol(name: str) -> str | None:
    mapping = {
        "天弘中证电网设备主题指数C": "561200",
        "广发中债7-10年期国开行债券指数E": "003376",
        "长城短债债券C": "007194",
        "嘉实中证高端装备细分50ETF联接C": "516320",
        "易方达科创50联接C": "588000",
        "天弘中证工业有色金属主题ETF联接C": "512400",
        "易方达人工智能ETF联接C": "159819",
        "嘉实中证机器人ETF联接C": "562500",
        "余额宝": "CNY",
    }
    for candidate, symbol in mapping.items():
        if candidate in name:
            return symbol
    return None


def parse_portfolio_snapshot(lines: list[OcrLine]) -> dict[str, Any]:
    texts = [item.text for item in lines]
    total_value = None
    cash_value = None
    for index, line in enumerate(texts):
        if "总金额" in line:
            total_value = _parse_next_numeric(texts, index, window=4)
        if line == "余额宝":
            cash_value = _parse_next_numeric(texts, index, window=4)

    holdings: list[dict[str, Any]] = []
    index = 0
    while index < len(texts):
        line = texts[index]
        if not _is_asset_name(line):
            index += 1
            continue
        name = line
        block: list[str] = []
        cursor = index + 1
        while cursor < len(texts) and not _is_asset_name(texts[cursor]):
            block.append(texts[cursor])
            if texts[cursor].startswith("占比"):
                if cursor + 1 < len(texts):
                    block.append(texts[cursor + 1])
                    cursor += 1
                break
            cursor += 1

        holding = {
            "name": name,
            "category": _infer_category(name),
            "asset_type": _infer_asset_type(name),
            "symbol": _infer_symbol(name),
            "theme": _infer_theme(name),
        }
        holding.update(_classify_holding_fields(block))
        holdings.append(holding)
        index = cursor + 1

    missing_fields: dict[str, list[str]] = {}
    for holding in holdings:
        missing = [field for field in ("symbol", "value") if holding.get(field) is None]
        if missing:
            missing_fields[holding["name"]] = missing

    return {
        "snapshot_type": "portfolio_overview",
        "summary": {
            "total_value": total_value,
            "cash_value": cash_value,
            "captured_at": None,
            "holding_count": len(holdings),
        },
        "holdings": holdings,
        "missing_fields": missing_fields,
        "ocr_lines": texts,
    }


def build_ocr_portfolio_import(
    portfolio_image_path: Path | None = None, gold_image_path: Path | None = None
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "status": "success",
        "portfolio_snapshot": None,
        "gold_snapshot": None,
        "merged_portfolio": None,
        "next_actions": [],
    }
    merged_assets: list[dict[str, Any]] = []
    total_value = 0.0

    if portfolio_image_path is not None:
        portfolio_lines = extract_ocr_lines(portfolio_image_path)
        portfolio_snapshot = parse_portfolio_snapshot(portfolio_lines)
        result["portfolio_snapshot"] = portfolio_snapshot
        merged_assets.extend(portfolio_snapshot["holdings"])
        if portfolio_snapshot["summary"]["total_value"] is not None:
            total_value += float(portfolio_snapshot["summary"]["total_value"])

    if gold_image_path is not None:
        gold_lines = extract_ocr_lines(gold_image_path)
        gold_snapshot = parse_gold_snapshot(gold_lines)
        result["gold_snapshot"] = gold_snapshot
        if gold_snapshot["asset"]["value"] is not None:
            merged_assets.append(gold_snapshot["asset"])
            total_value += float(gold_snapshot["asset"]["value"])

    result["merged_portfolio"] = {
        "updated_at": "",
        "assets": merged_assets,
        "total_value": round(total_value, 2),
    }
    result["next_actions"] = [
        "review_missing_fields_before_sync",
        "sync_to_portfolio_state_via_portfolio_editor",
        "refresh-prices",
        "signal-review",
        "weekly-review_or_monthly-review",
    ]
    return result
