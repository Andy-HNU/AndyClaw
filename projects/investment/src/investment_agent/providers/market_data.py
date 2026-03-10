from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


class MarketDataProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class MarketQuote:
    asset_code: str
    source: str
    trade_date: str
    close_price: float
    high_price: float | None
    low_price: float | None
    volume: float | None
    fetched_at: str

    @classmethod
    def from_dict(cls, payload: dict[str, object], default_source: str) -> "MarketQuote":
        return cls(
            asset_code=str(payload["asset_code"]),
            source=str(payload.get("source") or default_source),
            trade_date=str(payload["trade_date"]),
            close_price=float(payload["close_price"]),
            high_price=float(payload["high_price"]) if payload.get("high_price") is not None else None,
            low_price=float(payload["low_price"]) if payload.get("low_price") is not None else None,
            volume=float(payload["volume"]) if payload.get("volume") is not None else None,
            fetched_at=str(payload["fetched_at"]),
        )

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class MarketDataProvider:
    def get_latest_quotes(self, asset_codes: list[str]) -> list[MarketQuote]:
        raise NotImplementedError


class JsonFileMarketDataProvider(MarketDataProvider):
    def __init__(self, source_name: str, data_path: Path) -> None:
        self.source_name = source_name
        self.data_path = Path(data_path)

    def get_latest_quotes(self, asset_codes: list[str]) -> list[MarketQuote]:
        payload = json.loads(self.data_path.read_text(encoding="utf-8"))
        quotes_by_code = {
            str(item["asset_code"]): MarketQuote.from_dict(item, default_source=self.source_name)
            for item in payload["quotes"]
        }
        missing = [asset_code for asset_code in asset_codes if asset_code not in quotes_by_code]
        if missing:
            raise MarketDataProviderError(
                f"{self.source_name} missing quotes for: {', '.join(sorted(missing))}"
            )
        return [quotes_by_code[asset_code] for asset_code in asset_codes]


class FailingMarketDataProvider(MarketDataProvider):
    def __init__(self, source_name: str, message: str) -> None:
        self.source_name = source_name
        self.message = message

    def get_latest_quotes(self, asset_codes: list[str]) -> list[MarketQuote]:
        raise MarketDataProviderError(f"{self.source_name}: {self.message}")


def refresh_market_quotes(
    asset_codes: list[str],
    primary_provider: MarketDataProvider,
    backup_provider: MarketDataProvider | None = None,
) -> dict[str, object]:
    errors: list[dict[str, str]] = []
    providers = [primary_provider]
    if backup_provider is not None:
        providers.append(backup_provider)

    for index, provider in enumerate(providers):
        try:
            quotes = provider.get_latest_quotes(asset_codes)
            source = str(getattr(provider, "source_name", quotes[0].source if quotes else f"provider_{index}"))
            return {
                "status": "success",
                "used_backup": index > 0,
                "source": source,
                "quotes": [quote.to_dict() for quote in quotes],
                "errors": errors,
            }
        except MarketDataProviderError as exc:
            source_name = getattr(provider, "source_name", provider.__class__.__name__)
            errors.append({"source": str(source_name), "message": str(exc)})

    return {
        "status": "failed",
        "used_backup": False,
        "source": None,
        "quotes": [],
        "errors": errors,
        "message": "all configured market data providers failed",
    }
