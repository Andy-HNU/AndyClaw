from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone

from .models import NewsItem


ESCALATION_TERMS = (
    "attack",
    "strike",
    "missile",
    "sanction",
    "seize",
    "drill",
    "warning",
    "threat",
    "blockade",
    "surge",
)
DE_ESCALATION_TERMS = (
    "talk",
    "ceasefire",
    "truce",
    "deal",
    "reopen",
    "resume",
    "de-escalat",
    "negotia",
    "diplomat",
)


def classify_bucket(title: str) -> str:
    normalized = title.lower()
    if any(term in normalized for term in ESCALATION_TERMS):
        return "escalation"
    if any(term in normalized for term in DE_ESCALATION_TERMS):
        return "de-escalation"
    return "noise"


def render_report(
    topic: str,
    items: list[NewsItem],
    impact_template: list[str] | None = None,
    generated_at: datetime | None = None,
) -> str:
    generated = (generated_at or datetime.now(timezone.utc)).replace(microsecond=0)
    buckets = {
        "escalation": [item for item in items if classify_bucket(item.title) == "escalation"],
        "de-escalation": [item for item in items if classify_bucket(item.title) == "de-escalation"],
        "noise": [item for item in items if classify_bucket(item.title) == "noise"],
    }
    tier_counts = Counter(item.tier for item in items)
    top_tags = ", ".join(tag for tag, _ in Counter(item.query_tag for item in items).most_common(3)) or "none"
    lead = _lead_summary(topic, items, buckets, tier_counts, top_tags)
    news_lines = [
        f"- [{item.title}]({item.link}) | {item.source} | {item.published_at} | tier {item.tier} | tag {item.query_tag}"
        for item in items
    ] or ["- No items collected."]
    impact_lines = impact_template or [
        "- Gold theme: [safe-haven demand / no clear read / easing]",
        "- Bond theme: [duration bid / no clear read / yields higher on growth or supply shock]",
        "- Stock theme: [energy up / transport down / defense up / broad risk-off / neutral]",
        "- Watchlist: [oil majors, airlines, shippers, defense, EM FX]",
    ]

    lines = [
        f"# Watchboard Report: {topic}",
        "",
        f"- Generated at: {generated.isoformat()}",
        f"- Total items: {len(items)}",
        f"- Tier mix: A={tier_counts.get('A', 0)} B={tier_counts.get('B', 0)} C={tier_counts.get('C', 0)}",
        f"- Dominant query tags: {top_tags}",
        "",
        "## Telegram Brief",
        *render_telegram_summary(topic, items),
        "",
        "## Headline Summary",
        lead,
        "",
        "## Buckets",
        f"### Escalation ({len(buckets['escalation'])})",
        *_bucket_lines(buckets["escalation"]),
        "",
        f"### De-escalation ({len(buckets['de-escalation'])})",
        *_bucket_lines(buckets["de-escalation"]),
        "",
        f"### Noise ({len(buckets['noise'])})",
        *_bucket_lines(buckets["noise"]),
        "",
        "## Timeline (Chronological)",
        *render_timeline(items),
        "",
        "## Source-Cited News",
        *news_lines,
        "",
        "## Claim Check",
        *claim_check_lines(items),
        "",
        "## Portfolio Impact Template",
        *impact_lines,
    ]
    return "\n".join(lines).strip() + "\n"


def render_telegram_summary(topic: str, items: list[NewsItem]) -> list[str]:
    if not items:
        return [f"- {topic}: no fresh items."]
    bucket_counts = Counter(classify_bucket(item.title) for item in items)
    top_claim = top_claim_check(items)
    top_items = items[:3]
    lines = [
        f"- {topic}: E/D/N={bucket_counts.get('escalation', 0)}/{bucket_counts.get('de-escalation', 0)}/{bucket_counts.get('noise', 0)}",
        f"- Top claim-check: {top_claim}",
        "- Top sources:",
    ]
    lines.extend(
        f"  - tier {item.tier} | {item.source} | {item.title} | {item.link}"
        for item in top_items
    )
    return lines


def render_timeline(items: list[NewsItem]) -> list[str]:
    if not items:
        return ["- No events collected."]
    ordered = sorted(items, key=lambda item: item.published_at)
    return [f"- {item.published_at} | {item.title} ({item.source}, tier {item.tier})" for item in ordered]


def _lead_summary(
    topic: str,
    items: list[NewsItem],
    buckets: dict[str, list[NewsItem]],
    tier_counts: Counter,
    top_tags: str,
) -> str:
    if not items:
        return f"No items were collected for `{topic}`. Check feed reachability or expand the query set."
    dominant_bucket = max(buckets, key=lambda name: len(buckets[name]))
    return (
        f"Current signal leans **{dominant_bucket}** for `{topic}` based on {len(items)} normalized headlines. "
        f"Coverage is concentrated in tags `{top_tags}` with tier-A/B items totaling "
        f"{tier_counts.get('A', 0) + tier_counts.get('B', 0)}."
    )


def _bucket_lines(items: list[NewsItem]) -> list[str]:
    if not items:
        return ["- None."]
    return [f"- {item.title} ({item.source}, tier {item.tier})" for item in items[:5]]


def claim_check_lines(items: list[NewsItem]) -> list[str]:
    claims = [
        ("Oil to $200", ("oil", "$200", "200")),
        ("Shipping lane closure", ("closure", "closed", "blockade", "seize")),
        ("Immediate diplomatic breakthrough", ("deal", "talk", "ceasefire", "truce")),
    ]
    lines: list[str] = []
    for claim, needles in claims:
        supporting = [item for item in items if supports_claim(item.title.lower(), claim, needles)]
        related = [item for item in items if any(needle in item.title.lower() for needle in needles)]
        verdict = "unsupported in current headlines"
        if supporting:
            verdict = f"headline support found in {len(supporting)} item(s)"
        elif related:
            verdict = f"partial mentions only in {len(related)} item(s)"
        lines.append(f"- {claim}: {verdict}")
    return lines


def top_claim_check(items: list[NewsItem]) -> str:
    ranked = []
    for line in claim_check_lines(items):
        if "headline support found" in line:
            score = 2
        elif "partial mentions" in line:
            score = 1
        else:
            score = 0
        ranked.append((score, line.removeprefix("- ")))
    ranked.sort(key=lambda pair: pair[0], reverse=True)
    return ranked[0][1] if ranked else "no claim-check signal"


def supports_claim(title: str, claim: str, needles: tuple[str, ...]) -> bool:
    if claim == "Oil to $200":
        return "oil" in title and ("$200" in title or "200" in title)
    return any(needle in title for needle in needles)
