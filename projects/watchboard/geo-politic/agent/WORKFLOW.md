# Workflow

## Operator Loop

1. Pick a topic key from `system/topics.json`.
2. Run `run-topic` or `run-all`.
3. Review Telegram brief, buckets, timeline, and claim-check.
4. Tune `queries`, `source_preferences`, or tiers when quality drifts.

## Runtime Scheduler Integration (examples)

Use your scheduler/runtime of choice and call CLI directly. No hardcoded cron in code.

```bash
# every 30 min (example shell command for scheduler)
python3 -m geopolitics_watchboard.main run-topic --topic iran-hormuz --since-hours 6

# hourly, all topics
python3 -m geopolitics_watchboard.main run-all --since-hours 12
```

Output is deterministic and safe for downstream ingestion:

```text
/root/.openclaw/workspace/staging/reports/<topic>/<YYYY-MM-DD>/<YYYYMMDDTHHMMSSZ>.md
```

## Add A New Topic

1. Open `system/topics.json`.
2. Add a topic with `queries` and optional `source_preferences` + `impact_template`.
3. Validate:

```bash
python3 -m unittest discover -s tests -v
python3 -m geopolitics_watchboard.main run-topic --topic "your-topic"
```

## Output Contract

Every report should contain:

- Telegram brief (links + confidence tiers + top claim-check)
- headline summary
- escalation/de-escalation/noise buckets
- chronological timeline
- source-cited news list
- claim-check section
- portfolio impact template (topic override if defined)
