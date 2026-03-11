from __future__ import annotations

import importlib
import importlib.util
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


class IntradayDataProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class IntradayDriverQuote:
    driver_code: str
    driver_name: str
    price_change_pct: float
    volume_ratio: float | None
    amplitude_pct: float | None
    drawdown_from_high_pct: float | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "driver_code": self.driver_code,
            "driver_name": self.driver_name,
            "price_change_pct": self.price_change_pct,
            "volume_ratio": self.volume_ratio,
            "amplitude_pct": self.amplitude_pct,
            "drawdown_from_high_pct": self.drawdown_from_high_pct,
        }


class IntradayDataProvider:
    def get_intraday_proxy_inputs(self) -> dict[str, Any]:
        raise NotImplementedError


class JsonFileIntradayDataProvider(IntradayDataProvider):
    def __init__(self, source_name: str, data_path: Path) -> None:
        self.source_name = source_name
        self.data_path = Path(data_path)

    def get_intraday_proxy_inputs(self) -> dict[str, Any]:
        payload = json.loads(self.data_path.read_text(encoding="utf-8"))
        return dict(payload)


class AkshareIntradayDataProvider(IntradayDataProvider):
    source_name = "akshare-intraday"

    def __init__(self, mapping_path: Path) -> None:
        self.mapping_path = Path(mapping_path)

    @property
    def enabled(self) -> bool:
        return importlib.util.find_spec("akshare") is not None

    def get_intraday_proxy_inputs(self) -> dict[str, Any]:
        if not self.enabled:
            raise IntradayDataProviderError("akshare not installed")
        try:
            mapping = json.loads(self.mapping_path.read_text(encoding="utf-8"))
            items = list(mapping.get("drivers") or [])
            if not items:
                raise IntradayDataProviderError("driver mapping is empty")

            ak = importlib.import_module("akshare")
            spot_df = ak.stock_zh_a_spot_em()
            stock_lookup = {str(row.get("代码")): row for _, row in spot_df.iterrows()}

            drivers: list[IntradayDriverQuote] = []
            for item in items:
                driver_code = str(item["driver_code"])
                symbol = str(item.get("akshare_symbol") or "")
                if not symbol:
                    continue
                row = stock_lookup.get(symbol)
                if row is None:
                    continue
                latest = float(row["最新价"])
                pct = float(row["涨跌幅"])
                high = float(row["最高"])
                low = float(row["最低"])
                open_price = float(row["今开"])
                amplitude = (high - low) / open_price * 100 if open_price else None
                drivers.append(
                    IntradayDriverQuote(
                        driver_code=driver_code,
                        driver_name=str(item.get("driver_name") or row.get("名称") or driver_code),
                        price_change_pct=round(pct, 4),
                        volume_ratio=None,
                        amplitude_pct=round(amplitude, 4) if amplitude is not None else None,
                        drawdown_from_high_pct=round((latest - high) / high * 100, 4) if high else None,
                    )
                )

            if not drivers:
                raise IntradayDataProviderError("no mapped drivers were fetched")
            return {
                "status": "success",
                "data_quality": "real",
                "source": self.source_name,
                "as_of": datetime.now().astimezone().isoformat(timespec="seconds"),
                "drivers": [item.to_dict() for item in drivers],
            }
        except IntradayDataProviderError:
            raise
        except Exception as exc:
            raise IntradayDataProviderError(f"{self.source_name}: {exc}") from exc


def refresh_intraday_proxy_inputs(
    primary_provider: IntradayDataProvider,
    fallback_provider: IntradayDataProvider | None = None,
) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    providers = [primary_provider]
    if fallback_provider is not None:
        providers.append(fallback_provider)

    for index, provider in enumerate(providers):
        try:
            payload = provider.get_intraday_proxy_inputs()
            source = str(getattr(provider, "source_name", f"provider_{index}"))
            return {
                **payload,
                "status": "success",
                "source": source,
                "used_backup": index > 0,
                "errors": errors,
            }
        except IntradayDataProviderError as exc:
            source_name = getattr(provider, "source_name", provider.__class__.__name__)
            errors.append({"source": str(source_name), "message": str(exc)})

    return {
        "status": "failed",
        "reason": "all_intraday_providers_failed",
        "data_quality": "fallback",
        "source": None,
        "used_backup": False,
        "as_of": None,
        "drivers": [],
        "errors": errors,
    }
