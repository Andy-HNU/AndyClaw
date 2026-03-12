from __future__ import annotations

import json
from pathlib import Path

from .models import FeedQuery, FeedSpec


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def workspace_root() -> Path:
    current = project_root()
    for candidate in [current, *current.parents]:
        if (candidate / "AGENTS.md").exists() and (candidate / ".git").exists():
            return candidate
    return Path(__file__).resolve().parents[5]


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_source_config(config_path: Path | None = None) -> dict:
    path = config_path or project_root() / "system" / "sources.yaml"
    return _read_json(path)


def load_topics_registry(config_path: Path | None = None) -> dict:
    path = config_path or project_root() / "system" / "topics.json"
    return _read_json(path)


def feed_specs(config: dict, preferred_names: list[str] | None = None) -> list[FeedSpec]:
    preferred = set(preferred_names or [])
    feeds = [FeedSpec(**feed) for feed in config["feeds"]]
    if not preferred:
        return feeds
    filtered = [feed for feed in feeds if feed.name in preferred]
    return filtered or feeds


def topic_config(registry: dict, topic: str) -> dict:
    topic_def = registry.get("topics", {}).get(topic)
    if not topic_def:
        known = ", ".join(sorted(registry.get("topics", {})))
        raise ValueError(f"Unknown topic '{topic}'. Known topics: {known}")
    return topic_def


def topic_queries(registry: dict, topic: str) -> list[FeedQuery]:
    query_defs = topic_config(registry, topic).get("queries", [])
    if not query_defs:
        raise ValueError(f"Topic '{topic}' has no configured queries.")
    return [FeedQuery(tag=item["tag"], query=item["query"]) for item in query_defs]
