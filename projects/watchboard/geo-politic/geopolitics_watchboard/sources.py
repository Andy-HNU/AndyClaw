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


def load_source_config(config_path: Path | None = None) -> dict:
    path = config_path or project_root() / "system" / "sources.yaml"
    return json.loads(path.read_text(encoding="utf-8"))


def feed_specs(config: dict) -> list[FeedSpec]:
    return [FeedSpec(**feed) for feed in config["feeds"]]


def topic_queries(config: dict, topic: str) -> list[FeedQuery]:
    query_defs = config["default_queries"].get(topic)
    if not query_defs:
        known = ", ".join(sorted(config["default_queries"]))
        raise ValueError(f"Unknown topic '{topic}'. Known topics: {known}")
    return [FeedQuery(tag=item["tag"], query=item["query"]) for item in query_defs]

