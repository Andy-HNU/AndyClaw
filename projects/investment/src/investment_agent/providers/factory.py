from __future__ import annotations

import importlib
import importlib.util
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from investment_agent.config import ProjectPaths
from investment_agent.models.portfolio import Asset, PortfolioState
from investment_agent.providers.intraday_data import (
    AkshareIntradayDataProvider,
    IntradayDataProvider,
    JsonFileIntradayDataProvider,
)
from investment_agent.providers.market_data import (
    JsonFileMarketDataProvider,
    MarketDataProvider,
    MarketDataProviderError,
    MarketQuote,
)
from investment_agent.providers.news_data import (
    JsonFileNewsDataProvider,
    NewsDataProvider,
    NewsDataProviderError,
    NewsItem,
)


@dataclass(frozen=True)
class ProviderCapability:
    name: str
    enabled: bool
    reason: str

    def to_dict(self) -> dict[str, object]:
        return {"name": self.name, "enabled": self.enabled, "reason": self.reason}


def _load_portfolio_assets(path: Path) -> list[Asset]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    state = PortfolioState(updated_at=str(payload["updated_at"]), assets=[Asset.from_dict(item) for item in payload["assets"]])
    return state.assets


def _load_fixture_market_quotes(path: Path) -> dict[str, dict[str, Any]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return {str(item["asset_code"]): dict(item) for item in payload["quotes"]}


class DependencyBackedCapability:
    def __init__(self, source_name: str, dependency_name: str, install_hint: str) -> None:
        self.source_name = source_name
        self.dependency_name = dependency_name
        self.install_hint = install_hint

    @property
    def enabled(self) -> bool:
        return importlib.util.find_spec(self.dependency_name) is not None

    def capability(self) -> ProviderCapability:
        if self.enabled:
            return ProviderCapability(
                name=self.source_name,
                enabled=True,
                reason=f"{self.dependency_name} is installed and the adapter is enabled",
            )
        return ProviderCapability(
            name=self.source_name,
            enabled=False,
            reason=f"{self.dependency_name} is not installed; {self.install_hint}",
        )

class AkshareMarketProvider(MarketDataProvider, DependencyBackedCapability):
    def __init__(self, paths: ProjectPaths) -> None:
        DependencyBackedCapability.__init__(
            self,
            source_name="akshare-market",
            dependency_name="akshare",
            install_hint="install akshare before enabling the real market-data adapter",
        )
        self.assets_by_code = {asset.theme or asset.name: asset for asset in _load_portfolio_assets(paths.portfolio_state_path)}
        self.fixture_quotes = _load_fixture_market_quotes(paths.market_data_primary_path)

    def _build_fixture_quote(self, asset_code: str) -> MarketQuote:
        payload = self.fixture_quotes.get(asset_code)
        if payload is None:
            raise MarketDataProviderError(f"{self.source_name} missing local fallback quote for {asset_code}")
        payload = dict(payload)
        payload["source"] = f"{self.source_name}-fixture"
        return MarketQuote.from_dict(payload, default_source=self.source_name)

    def get_latest_quotes(self, asset_codes: list[str]) -> list[MarketQuote]:
        if not self.enabled:
            raise MarketDataProviderError(
                f"{self.source_name} unavailable because dependency {self.dependency_name} is not installed"
            )
        try:
            ak = importlib.import_module("akshare")
            etf_df = ak.fund_etf_spot_em()
            etf_lookup = {
                str(row["代码"]): row
                for _, row in etf_df.iterrows()
            }

            open_fund_df = ak.fund_value_estimation_em(symbol="全部")
            estimate_column = next(
                column for column in open_fund_df.columns if column.endswith("估算数据-估算值")
            )
            published_column = next(
                column for column in open_fund_df.columns if column.endswith("公布数据-单位净值")
            )
            open_fund_lookup = {
                str(row["基金代码"]): row
                for _, row in open_fund_df.iterrows()
            }
            gold_histories: dict[str, Any] = {}

            results: list[MarketQuote] = []
            for asset_code in asset_codes:
                asset = self.assets_by_code.get(asset_code)
                if asset is None:
                    results.append(self._build_fixture_quote(asset_code))
                    continue

                if asset.asset_type == "commodity":
                    symbol = asset.symbol or "Au99.99"
                    if symbol not in gold_histories:
                        gold_histories[symbol] = ak.spot_hist_sge(symbol=symbol)
                    gold_df = gold_histories[symbol]
                    latest_row = gold_df.iloc[-1]
                    results.append(
                        MarketQuote(
                            asset_code=asset_code,
                            source=self.source_name,
                            trade_date=str(latest_row["date"]),
                            close_price=float(latest_row["close"]),
                            high_price=float(latest_row["high"]),
                            low_price=float(latest_row["low"]),
                            volume=None,
                            fetched_at=str(latest_row["date"]),
                        )
                    )
                    continue

                if asset.asset_type in {"etf", "index_fund", "thematic_fund"} and asset.symbol in etf_lookup:
                    row = etf_lookup[str(asset.symbol)]
                    results.append(
                        MarketQuote(
                            asset_code=asset_code,
                            source=self.source_name,
                            trade_date=str(row.get("数据日期") or row.get("更新时间") or ""),
                            close_price=float(row["最新价"]),
                            high_price=float(row["最高价"]) if row.get("最高价") is not None else None,
                            low_price=float(row["最低价"]) if row.get("最低价") is not None else None,
                            volume=float(row["成交量"]) if row.get("成交量") is not None else None,
                            fetched_at=str(row.get("更新时间") or row.get("数据日期") or ""),
                        )
                    )
                    continue

                if asset.asset_type == "bond_fund" and asset.symbol in open_fund_lookup:
                    row = open_fund_lookup[str(asset.symbol)]
                    estimate = float(row[estimate_column])
                    published = float(row[published_column])
                    results.append(
                        MarketQuote(
                            asset_code=asset_code,
                            source=self.source_name,
                            trade_date=estimate_column.split("-估算数据-")[0],
                            close_price=estimate,
                            high_price=max(estimate, published),
                            low_price=min(estimate, published),
                            volume=None,
                            fetched_at=estimate_column.split("-估算数据-")[0],
                        )
                    )
                    continue

                results.append(self._build_fixture_quote(asset_code))

            return results
        except Exception as exc:
            raise MarketDataProviderError(f"{self.source_name}: {exc}") from exc


class AkshareNewsProvider(NewsDataProvider, DependencyBackedCapability):
    def __init__(self, paths: ProjectPaths) -> None:
        DependencyBackedCapability.__init__(
            self,
            source_name="akshare-news",
            dependency_name="akshare",
            install_hint="install akshare before enabling the real news adapter",
        )
        self.assets_by_code = {asset.theme or asset.name: asset for asset in _load_portfolio_assets(paths.portfolio_state_path)}

    def _news_keywords(self) -> list[str]:
        candidates = []
        for asset in self.assets_by_code.values():
            if asset.category == "cash":
                continue
            keyword = re.sub(r"ETF|指数A|指数C|指数E|基金", "", asset.name).strip()
            if keyword and keyword not in candidates:
                candidates.append(keyword)
        return candidates[:3]

    def _extract_date(self, url: str) -> str:
        match = re.search(r"(20\d{2}-\d{2}-\d{2})", url)
        return match.group(1) if match else ""

    def get_latest_news(self, limit: int | None = None) -> list[NewsItem]:
        if not self.enabled:
            raise NewsDataProviderError(
                f"{self.source_name} unavailable because dependency {self.dependency_name} is not installed"
            )

        try:
            ak = importlib.import_module("akshare")
            items: list[NewsItem] = []
            seen: set[str] = set()

            for keyword in self._news_keywords():
                try:
                    df = ak.stock_news_em(symbol=keyword)
                except Exception:
                    continue
                for _, row in df.head(3).iterrows():
                    url = str(row["新闻链接"])
                    dedupe_key = url or str(row["新闻标题"])
                    if dedupe_key in seen:
                        continue
                    seen.add(dedupe_key)
                    published_at = str(row["发布时间"]).split(" ")[0]
                    items.append(
                        NewsItem(
                            source=self.source_name,
                            title=str(row["新闻标题"]),
                            summary=str(row["新闻内容"]),
                            url=url,
                            published_at=published_at,
                            topic=str(row["关键词"]),
                            sentiment_hint="watch",
                            fetched_at=str(row["发布时间"]),
                        )
                    )
                    if limit is not None and len(items) >= limit:
                        return items[:limit]

            try:
                macro_df = ak.stock_news_main_cx()
            except Exception:
                macro_df = None
            if macro_df is not None:
                for _, row in macro_df.head(max(limit or 5, 3)).iterrows():
                    url = str(row["url"])
                    dedupe_key = url or str(row["summary"])
                    if dedupe_key in seen:
                        continue
                    seen.add(dedupe_key)
                    summary = str(row["summary"])
                    items.append(
                        NewsItem(
                            source=f"{self.source_name}-caixin",
                            title=summary[:40],
                            summary=summary,
                            url=url,
                            published_at=self._extract_date(url),
                            topic=str(row["tag"]),
                            sentiment_hint="neutral",
                            fetched_at=self._extract_date(url),
                        )
                    )
                    if limit is not None and len(items) >= limit:
                        return items[:limit]

            if not items:
                raise NewsDataProviderError(f"{self.source_name} returned no news items")
            return items[:limit] if limit is not None else items
        except NewsDataProviderError:
            raise
        except Exception as exc:
            raise NewsDataProviderError(f"{self.source_name}: {exc}") from exc


class EFinanceFundProvider(DependencyBackedCapability):
    def __init__(self) -> None:
        super().__init__(
            source_name="efinance-fund",
            dependency_name="efinance",
            install_hint="install efinance before enabling the real market-data adapter",
        )


def build_provider_capabilities(paths: ProjectPaths) -> list[ProviderCapability]:
    providers: list[ProviderCapability] = [
        AkshareMarketProvider(paths).capability(),
        AkshareNewsProvider(paths).capability(),
        EFinanceFundProvider().capability(),
        ProviderCapability(
            name="akshare-intraday",
            enabled=AkshareIntradayDataProvider(paths.intraday_driver_mapping_path).enabled,
            reason=(
                "akshare is installed and intraday proxy fetcher is enabled"
                if AkshareIntradayDataProvider(paths.intraday_driver_mapping_path).enabled
                else "akshare is not installed; install akshare before enabling intraday real fetcher"
            ),
        ),
        ProviderCapability(
            name="mock-primary",
            enabled=True,
            reason=f"local fixture available at {paths.market_data_primary_path.name}",
        ),
        ProviderCapability(
            name="mock-backup",
            enabled=True,
            reason=f"local fixture available at {paths.market_data_backup_path.name}",
        ),
    ]
    return providers


def build_default_market_data_chain(paths: ProjectPaths) -> list[MarketDataProvider]:
    akshare_provider = AkshareMarketProvider(paths)
    if akshare_provider.enabled:
        return [
            akshare_provider,
            JsonFileMarketDataProvider("mock-primary", paths.market_data_primary_path),
        ]
    return [
        JsonFileMarketDataProvider("mock-primary", paths.market_data_primary_path),
        JsonFileMarketDataProvider("mock-backup", paths.market_data_backup_path),
    ]


def build_default_news_data_chain(paths: ProjectPaths) -> list[NewsDataProvider]:
    akshare_provider = AkshareNewsProvider(paths)
    if akshare_provider.enabled:
        return [
            akshare_provider,
            JsonFileNewsDataProvider("mock-news-primary", paths.news_data_primary_path),
        ]
    return [
        JsonFileNewsDataProvider("mock-news-primary", paths.news_data_primary_path),
        JsonFileNewsDataProvider("mock-news-backup", paths.news_data_backup_path),
    ]


def build_default_intraday_data_chain(paths: ProjectPaths) -> list[IntradayDataProvider]:
    akshare_provider = AkshareIntradayDataProvider(paths.intraday_driver_mapping_path)
    if akshare_provider.enabled:
        return [
            akshare_provider,
            JsonFileIntradayDataProvider("mock-intraday-fallback", paths.intraday_realtime_path),
        ]
    return [
        JsonFileIntradayDataProvider("mock-intraday-primary", paths.intraday_realtime_path),
    ]
