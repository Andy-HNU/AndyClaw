from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


class NewsDataProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class NewsItem:
    source: str
    title: str
    summary: str
    url: str
    published_at: str
    topic: str
    sentiment_hint: str
    fetched_at: str

    @classmethod
    def from_dict(cls, payload: dict[str, object], default_source: str) -> "NewsItem":
        return cls(
            source=str(payload.get("source") or default_source),
            title=str(payload["title"]),
            summary=str(payload.get("summary") or ""),
            url=str(payload.get("url") or ""),
            published_at=str(payload.get("published_at") or ""),
            topic=str(payload.get("topic") or "uncategorized"),
            sentiment_hint=str(payload.get("sentiment_hint") or "neutral"),
            fetched_at=str(payload["fetched_at"]),
        )

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class NewsDataProvider:
    def get_latest_news(self, limit: int | None = None) -> list[NewsItem]:
        raise NotImplementedError


class JsonFileNewsDataProvider(NewsDataProvider):
    def __init__(self, source_name: str, data_path: Path) -> None:
        self.source_name = source_name
        self.data_path = Path(data_path)

    def get_latest_news(self, limit: int | None = None) -> list[NewsItem]:
        payload = json.loads(self.data_path.read_text(encoding="utf-8"))
        items = [
            NewsItem.from_dict(item, default_source=self.source_name)
            for item in payload["news"]
        ]
        if not items:
            raise NewsDataProviderError(f"{self.source_name} returned no news items")
        return items[:limit] if limit is not None else items


class FailingNewsDataProvider(NewsDataProvider):
    def __init__(self, source_name: str, message: str) -> None:
        self.source_name = source_name
        self.message = message

    def get_latest_news(self, limit: int | None = None) -> list[NewsItem]:
        raise NewsDataProviderError(f"{self.source_name}: {self.message}")


def refresh_news_items(
    primary_provider: NewsDataProvider,
    backup_provider: NewsDataProvider | None = None,
    limit: int = 5,
) -> dict[str, object]:
    errors: list[dict[str, str]] = []
    providers = [primary_provider]
    if backup_provider is not None:
        providers.append(backup_provider)

    for index, provider in enumerate(providers):
        try:
            items = provider.get_latest_news(limit=limit)
            source = items[0].source if items else f"provider_{index}"
            return {
                "status": "success",
                "used_backup": index > 0,
                "source": source,
                "news": [item.to_dict() for item in items],
                "errors": errors,
            }
        except NewsDataProviderError as exc:
            source_name = getattr(provider, "source_name", provider.__class__.__name__)
            errors.append({"source": str(source_name), "message": str(exc)})

    return {
        "status": "failed",
        "used_backup": False,
        "source": None,
        "news": [],
        "errors": errors,
        "message": "all configured news providers failed",
    }
