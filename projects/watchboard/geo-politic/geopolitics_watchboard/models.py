from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FeedQuery:
    tag: str
    query: str


@dataclass(frozen=True)
class FeedSpec:
    name: str
    kind: str
    url: str


@dataclass(frozen=True)
class NewsItem:
    title: str
    source: str
    published_at: str
    link: str
    query_tag: str
    tier: str

