from __future__ import annotations

import importlib.util
from dataclasses import dataclass

from investment_agent.config import ProjectPaths
from investment_agent.providers.market_data import JsonFileMarketDataProvider, MarketDataProvider


@dataclass(frozen=True)
class ProviderCapability:
    name: str
    enabled: bool
    reason: str

    def to_dict(self) -> dict[str, object]:
        return {"name": self.name, "enabled": self.enabled, "reason": self.reason}


class DependencyBackedProvider(MarketDataProvider):
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
                reason=f"{self.dependency_name} is installed and adapter can be completed next",
            )
        return ProviderCapability(
            name=self.source_name,
            enabled=False,
            reason=f"{self.dependency_name} is not installed; {self.install_hint}",
        )

    def get_latest_quotes(self, asset_codes: list[str]) -> list[object]:
        raise NotImplementedError(
            f"{self.source_name} adapter scaffolding exists, but runtime mapping is not yet implemented"
        )


class AkshareETFProvider(DependencyBackedProvider):
    def __init__(self) -> None:
        super().__init__(
            source_name="akshare-etf",
            dependency_name="akshare",
            install_hint="install akshare before enabling the real market-data adapter",
        )


class EFinanceFundProvider(DependencyBackedProvider):
    def __init__(self) -> None:
        super().__init__(
            source_name="efinance-fund",
            dependency_name="efinance",
            install_hint="install efinance before enabling the real market-data adapter",
        )


def build_provider_capabilities(paths: ProjectPaths) -> list[ProviderCapability]:
    providers: list[ProviderCapability] = [
        AkshareETFProvider().capability(),
        EFinanceFundProvider().capability(),
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
    return [
        JsonFileMarketDataProvider("mock-primary", paths.market_data_primary_path),
        JsonFileMarketDataProvider("mock-backup", paths.market_data_backup_path),
    ]
