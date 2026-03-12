# Workflow

## Operator Loop

1. Choose a topic key from `system/sources.yaml` or add a new one.
2. Run the CLI for that topic.
3. Review the markdown dashboard for headline quality, tier mix, and noisy feeds.
4. Adjust source tiers or query tags if the report is too sparse or too noisy.

## Add A New Topic

1. Open `system/sources.yaml`.
2. Add a new entry under `default_queries`.
3. Reuse existing feed templates unless the topic needs a dedicated feed.
4. Validate with:

```bash
python3 -m unittest discover -s tests -v
python3 -m geopolitics_watchboard.main run --topic "your-topic"
```

## Source Hygiene

- Keep official ministries, regulators, and primary institutions in tier A.
- Keep large wire services and established outlets in tier B unless there is a reason to promote or demote them.
- Use tier C for aggregators, niche feeds, or exploratory sources.

## Output Contract

Every report should contain:

- headline summary
- escalation/de-escalation/noise buckets
- source-cited news list
- claim-check section
- portfolio impact template
