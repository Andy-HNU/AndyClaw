# Watchboard / Geo-Politic MVP

## Goal

Build a small, runnable Python watchboard that can monitor geopolitical topics across multiple regions, normalize source items, tier source confidence, and render a markdown dashboard suitable for further analyst review.

## Scope

- Topic-first design, not region-locked.
- Config-driven source tiers and default search queries.
- Stdlib-first implementation.
- Output goes to the shared workspace staging area so other tools can consume reports.

## MVP Features

- Fetch RSS/search feeds for a requested topic.
- Normalize `title`, `source`, `published_at`, `link`, and `query_tag`.
- Assign confidence tiers from configured source lists A/B/C.
- Bucket headlines into escalation, de-escalation, and noise.
- Render a markdown dashboard with summary, cited news, claim checks, and portfolio impact placeholders.
- Provide tests for parsing, tiering, and report rendering.

## Non-Goals

- No browser automation.
- No LLM dependency.
- No coupling to the investment project beyond a documented integration note.

## Layout

- `geopolitics_watchboard/`: runnable package and CLI.
- `system/sources.yaml`: JSON-compatible YAML source registry and default queries.
- `agent/WORKFLOW.md`: operator workflow for extending topics/sources.
- `samples/`: sample rendered output.

