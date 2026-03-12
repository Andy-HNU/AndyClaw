from __future__ import annotations

from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
from email.utils import parsedate_to_datetime
from html import unescape
import re
from typing import Iterable
from urllib.parse import parse_qsl, quote_plus, urlencode, urlparse, urlunparse
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

from .models import FeedSpec, NewsItem


USER_AGENT = "watchboard-geo-politic/0.1"
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}
FINAL_URL_PARAM_NAMES = {
    "dest",
    "destination",
    "redirect",
    "redirect_url",
    "r",
    "target",
    "u",
    "url",
}


def fetch_feed_text(url: str, timeout: int = 15) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def feed_url(feed: FeedSpec, query: str) -> str:
    return feed.url.format(query=quote_plus(query))


def host_from_url(url: str) -> str:
    host = urlparse(url).netloc.lower()
    return host[4:] if host.startswith("www.") else host


def normalize_publisher_name(value: str) -> str:
    lowered = value.lower()
    collapsed = re.sub(r"[^\w]+", " ", lowered)
    return " ".join(collapsed.split())


def extract_candidate_urls(url: str) -> list[str]:
    candidates: list[str] = []
    queue = [url]
    seen: set[str] = set()
    while queue:
        current = queue.pop(0)
        if not current or current in seen:
            continue
        seen.add(current)
        candidates.append(current)
        parsed = urlparse(current)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True):
            if value.startswith(("http://", "https://")) or key.lower() in FINAL_URL_PARAM_NAMES:
                if value.startswith(("http://", "https://")):
                    queue.append(value)
    return candidates


def candidate_hostnames(url: str) -> list[str]:
    hosts: list[str] = []
    seen: set[str] = set()
    for candidate in extract_candidate_urls(url):
        host = host_from_url(candidate)
        if host and host not in seen:
            seen.add(host)
            hosts.append(host)
    return hosts


def preferred_hostname(url: str) -> str:
    hosts = candidate_hostnames(url)
    return hosts[-1] if hosts else ""


def _tier_entries(config: dict, tier: str) -> list[dict]:
    entries: list[dict] = []
    for raw in config.get("tiers", {}).get(tier, []):
        if isinstance(raw, str):
            entries.append({"domains": [raw], "aliases": []})
            continue
        entries.append(
            {
                "domains": [domain.lower() for domain in raw.get("domains", [])],
                "aliases": [normalize_publisher_name(alias) for alias in raw.get("aliases", [])],
            }
        )
    return entries


def assign_tier(link: str, config: dict, source: str | None = None) -> str:
    hosts = candidate_hostnames(link)
    normalized_source = normalize_publisher_name(source or "")
    for tier in ("A", "B", "C"):
        for entry in _tier_entries(config, tier):
            for domain in entry["domains"]:
                if any(host == domain or host.endswith(f".{domain}") for host in hosts):
                    return tier
            if normalized_source and normalized_source in entry["aliases"]:
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
        source = _safe_text(node.findtext("source")) or preferred_hostname(link) or feed_name
        published = parse_published(node.findtext("pubDate"))
        if title and link:
            items.append(
                NewsItem(
                    title=title,
                    source=source,
                    published_at=published,
                    link=link,
                    query_tag=query_tag,
                    tier=assign_tier(link, config, source=source),
                )
            )
    return items


def _parse_atom(root: ET.Element, feed_name: str, query_tag: str, config: dict) -> list[NewsItem]:
    items: list[NewsItem] = []
    for node in root.findall("atom:entry", ATOM_NS):
        title = _safe_text(node.findtext("atom:title", default="", namespaces=ATOM_NS))
        link_node = node.find("atom:link", ATOM_NS)
        link = link_node.attrib.get("href", "") if link_node is not None else ""
        source = preferred_hostname(link) or feed_name
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
                    tier=assign_tier(link, config, source=source),
                )
            )
    return items


def dedupe_items(items: Iterable[NewsItem]) -> list[NewsItem]:
    ordered: list[NewsItem] = []
    for item in sorted(items, key=lambda news: news.published_at, reverse=True):
        if _is_near_duplicate(item, ordered):
            continue
        ordered.append(item)
    return ordered


def _is_near_duplicate(item: NewsItem, existing: list[NewsItem]) -> bool:
    link = _canonical_link(item.link)
    title = _normalize_title(item.title)
    for seen in existing:
        seen_link = _canonical_link(seen.link)
        if link == seen_link:
            return True
        ratio = SequenceMatcher(None, title, _normalize_title(seen.title)).ratio()
        if ratio >= 0.9:
            return True
    return False


def _canonical_link(url: str) -> str:
    parsed = urlparse(url)
    keep = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True) if not k.lower().startswith("utm_")]
    return urlunparse((parsed.scheme, parsed.netloc.lower(), parsed.path.rstrip("/"), "", urlencode(sorted(keep)), ""))


def _normalize_title(title: str) -> str:
    collapsed = " ".join(title.lower().replace("-", " ").split())
    return "".join(ch for ch in collapsed if ch.isalnum() or ch.isspace())


def collect_items(topic: str, topic_cfg: dict, source_cfg: dict, since_hours: int | None = None) -> list[NewsItem]:
    from .sources import feed_specs, topic_queries

    collected: list[NewsItem] = []
    preferred_feeds = topic_cfg.get("source_preferences", {}).get("feeds")
    for query in topic_queries({"topics": {topic: topic_cfg}}, topic):
        for feed in feed_specs(source_cfg, preferred_feeds):
            try:
                xml_text = fetch_feed_text(feed_url(feed, query.query))
                collected.extend(parse_feed(xml_text, feed.name, query.tag, source_cfg))
            except Exception:
                continue

    deduped = dedupe_items(collected)
    if since_hours is None:
        return deduped
    cutoff = datetime.now(timezone.utc) - timedelta(hours=since_hours)
    return [item for item in deduped if datetime.fromisoformat(item.published_at) >= cutoff]


def _safe_text(value: str | None) -> str:
    return unescape((value or "").strip())
