# watchboard / geo-politic

`watchboard / geo-politic` is a small Python MVP for monitoring geopolitical developments across multiple topics and regions. The first runnable topic can be `iran-hormuz`, but the project is intentionally generalized so the same pipeline can be extended to Taiwan Strait, Red Sea shipping, Russia/NATO, energy chokepoints, sanctions, elections, or any future region/topic added to the source config.

The package import path remains `geopolitics_watchboard` so the CLI stays stable:

```bash
python3 -m geopolitics_watchboard.main run --topic "iran-hormuz"
```

The command fetches configured RSS/search feeds, normalizes headlines, assigns source confidence tiers, and writes a markdown dashboard to `/root/.openclaw/workspace/staging/reports`.

## Project Layout

- `PROJECT.md`: scope and MVP contract.
- `agent/WORKFLOW.md`: how to add new topics and source tiers.
- `system/sources.yaml`: tier registry and default topic queries.
- `geopolitics_watchboard/`: CLI, fetcher, normalization, and renderer.
- `tests/`: basic parsing, tiering, and report tests.
- `samples/iran-hormuz-report.md`: sample dashboard output.

## Run

From this directory:

```bash
python3 -m unittest discover -s tests -v
python3 -m geopolitics_watchboard.main run --topic "iran-hormuz"
```

The CLI prints the output file path after rendering the report.

## Extend To More Regions Or Topics

1. Add or edit a topic entry in `system/sources.yaml`.
2. Add query tags that represent the scenario you want to track.
3. Optionally add or refine tier A/B/C source hostnames.
4. Run the CLI with the new topic key.

The renderer is topic-agnostic. Any topic with configured queries can reuse the same headline summary, bucket classification, claim-check section, and portfolio impact template.

## Source Tiers

- Tier A: primary or official sources.
- Tier B: major mainstream reporting and wire services.
- Tier C: secondary aggregators and lower-confidence signal sources.

These tiers are heuristic confidence markers for dashboard triage, not truth guarantees.

## Investment Integration Note

This project is independent from `projects/investment`. The intended integration point is file-based: the investment workflow can ingest rendered markdown from `/root/.openclaw/workspace/staging/reports` or call this CLI as a pre-step when geopolitical context is needed.
