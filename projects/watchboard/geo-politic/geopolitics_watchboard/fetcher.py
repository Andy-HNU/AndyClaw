from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from typing import Iterable
from urllib.parse import quote_plus, urlparse
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

from .models import FeedSpec, NewsItem


USER_AGENT = "watchboard-geo-politic/0.1"
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}


def fetch_feed_text(url: str, timeout: int = 15) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def feed_url(feed: FeedSpec, query: str) -> str:
    return feed.url.format(query=quote_plus(query))


def host_from_url(url: str) -> str:
    host = urlparse(url).netloc.lower()
    return host[4:] if host.startswith("www.") else host


def assign_tier(link: str, config: dict) -> str:
    host = host_from_url(link)
    for tier in ("A", "B", "C"):
        if any(host == domain or host.endswith(f".{domain}") for domain in config["tiers"][tier]):
            return tier
    return "C"


def parse_published(value: str | None) -> str:
    if not value:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    try:
        parsed = parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat()
    except (TypeError, ValueError, IndexError, OverflowError):
        pass
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat()
    except ValueError:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def parse_feed(xml_text: str, feed_name: str, query_tag: str, config: dict) -> list[NewsItem]:
    root = ET.fromstring(xml_text)
    if root.tag.endswith("feed"):
        return _parse_atom(root, feed_name, query_tag, config)
    return _parse_rss(root, feed_name, query_tag, config)


def _parse_rss(root: ET.Element, feed_name: str, query_tag: str, config: dict) -> list[NewsItem]:
    items: list[NewsItem] = []
    for node in root.findall(".//item"):
        title = _safe_text(node.findtext("title"))
        link = _safe_text(node.findtext("link"))
        source = _safe_text(node.findtext("source")) or host_from_url(link) or feed_name
        published = parse_published(node.findtext("pubDate"))
        if title and link:
            items.append(
                NewsItem(
                    title=title,
                    source=source,
                    published_at=published,
                    link=link,
                    query_tag=query_tag,
                    tier=assign_tier(link, config),
                )
            )
    return items


def _parse_atom(root: ET.Element, feed_name: str, query_tag: str, config: dict) -> list[NewsItem]:
    items: list[NewsItem] = []
    for node in root.findall("atom:entry", ATOM_NS):
        title = _safe_text(node.findtext("atom:title", default="", namespaces=ATOM_NS))
        link_node = node.find("atom:link", ATOM_NS)
        link = link_node.attrib.get("href", "") if link_node is not None else ""
        source = host_from_url(link) or feed_name
        published = parse_published(
            node.findtext("atom:published", default="", namespaces=ATOM_NS)
            or node.findtext("atom:updated", default="", namespaces=ATOM_NS)
        )
        if title and link:
            items.append(
                NewsItem(
                    title=title,
                    source=source,
                    published_at=published,
                    link=link,
                    query_tag=query_tag,
                    tier=assign_tier(link, config),
                )
            )
    return items


def dedupe_items(items: Iterable[NewsItem]) -> list[NewsItem]:
    seen: set[tuple[str, str]] = set()
    ordered: list[NewsItem] = []
    for item in sorted(items, key=lambda news: news.published_at, reverse=True):
        key = (item.title.lower(), item.link)
        if key in seen:
            continue
        seen.add(key)
        ordered.append(item)
    return ordered


def collect_items(topic: str, config: dict) -> list[NewsItem]:
    from .sources import feed_specs, topic_queries

    collected: list[NewsItem] = []
    for query in topic_queries(config, topic):
        for feed in feed_specs(config):
            try:
                xml_text = fetch_feed_text(feed_url(feed, query.query))
                collected.extend(parse_feed(xml_text, feed.name, query.tag, config))
            except Exception:
                continue
    return dedupe_items(collected)


def _safe_text(value: str | None) -> str:
    return unescape((value or "").strip())
