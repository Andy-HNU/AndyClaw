# watchboard / geo-politic

`watchboard / geo-politic` is a Python watchboard for monitoring geopolitical developments across multiple topics and regions.

## What changed in v1.1

- Multi-topic registry in `system/topics.json`.
- Scheduler-ready CLI (`run-topic`, `run-all`, `--since-hours`).
- Deterministic output paths with topic/date/timestamp folders.
- Telegram-friendly summary block in each report.
- Near-duplicate dedup and chronological timeline section.

## Project Layout

- `system/sources.yaml`: global feed and source-tier config.
- `system/topics.json`: per-topic queries, source preferences, optional impact template.
- `geopolitics_watchboard/main.py`: CLI command surface.
- `geopolitics_watchboard/fetcher.py`: fetch + normalize + dedup.
- `geopolitics_watchboard/report.py`: report rendering (telegram summary, buckets, timeline, claim-check).
- `tests/`: unit tests for topic loading, dedup, timeline, and summary rendering.

## Commands

```bash
python3 -m unittest discover -s tests -v

# one topic
python3 -m geopolitics_watchboard.main run-topic --topic iran-hormuz --since-hours 24

# all topics in registry
python3 -m geopolitics_watchboard.main run-all --since-hours 12
```

Backward-compatible alias still works:

```bash
python3 -m geopolitics_watchboard.main run --topic iran-hormuz
```

## Output locations

Reports are written to:

```text
/root/.openclaw/workspace/staging/reports/<topic>/<YYYY-MM-DD>/<YYYYMMDDTHHMMSSZ>.md
```

Example:

```text
/root/.openclaw/workspace/staging/reports/iran-hormuz/2026-03-12/20260312T045500Z.md
```

## Add a new topic

1. Edit `system/topics.json`.
2. Add a topic key under `topics` with:
   - `queries`: list of `{tag, query}`
   - `source_preferences.feeds` (optional)
   - `impact_template` (optional)
3. Run `run-topic` with your topic key.

## Source tiers

- Tier A: primary/official sources
- Tier B: major mainstream/wire sources
- Tier C: secondary/aggregator signal
