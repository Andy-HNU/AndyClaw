# OpenClaw Acceptance Commands

Use these commands when OpenClaw or Codex needs to verify the current
investment implementation slice.

## SQLite bootstrap
```bash
cd /root/.openclaw/workspace/projects/investment
PYTHONPATH=src python3 -m investment_agent.main init-db
```

Expected:
- database file exists
- `portfolio_assets` seeded
- latest snapshot present

## Portfolio summary
```bash
cd /root/.openclaw/workspace/projects/investment
PYTHONPATH=src python3 -m investment_agent.main portfolio-summary
```

Expected:
- `total_value` returned
- `allocations_pct` contains `gold`, `bond`, `stock`, `cash`
- `deviations_pct` returned

## Rebalance review
```bash
cd /root/.openclaw/workspace/projects/investment
PYTHONPATH=src python3 -m investment_agent.main rebalance-check
```

Expected:
- `triggered` boolean returned
- `breaches` list returned
- priority action returned

## Refresh prices
```bash
cd /root/.openclaw/workspace/projects/investment
PYTHONPATH=src python3 -m investment_agent.main refresh-prices
```

Expected:
- `refresh_result.status` is `success`
- `inserted_rows` matches current asset count
- `refresh_result.source` returned
- if `akshare` is installed, the source should prefer the real provider before mock fallback
- gold should refresh from the real commodity adapter rather than the local fixture

## Provider capabilities
```bash
cd /root/.openclaw/workspace/projects/investment
PYTHONPATH=src python3 -m investment_agent.main provider-capabilities
```

Expected:
- provider list returned
- enabled real providers explain that their adapters are active
- local mock providers remain enabled

## Persist analysis
```bash
cd /root/.openclaw/workspace/projects/investment
PYTHONPATH=src python3 -m investment_agent.main persist-analysis
```

Expected:
- `analysis_result_id` returned
- latest analysis includes allocation/deviation payloads
- row written into `analysis_results`

## Persist rebalance review
```bash
cd /root/.openclaw/workspace/projects/investment
PYTHONPATH=src python3 -m investment_agent.main persist-rebalance
```

Expected:
- persisted suggestion returned
- open `allocation_drift` signals returned
- risk signal count matches rebalance breach count

## Monthly plan
```bash
cd /root/.openclaw/workspace/projects/investment
PYTHONPATH=src python3 -m investment_agent.main monthly-plan
```

Expected:
- `status` returned
- `underweight_categories` returned
- recommendation amounts sum to the configured monthly budget

## Monthly review
```bash
cd /root/.openclaw/workspace/projects/investment
PYTHONPATH=src python3 -m investment_agent.main monthly-review
```

Expected:
- `status` is `success`
- `price_refresh.status` is `success`
- `news_refresh.status` is `success`
- `monthly_plan` returned
- `report.report_type` is `monthly`
- workflow persists supporting data and a report row

## Weekly review
```bash
cd /root/.openclaw/workspace/projects/investment
PYTHONPATH=src python3 -m investment_agent.main weekly-review
```

Expected:
- `status` is `success`
- `price_refresh.status` is `success`
- `news_refresh.status` is `success`
- `report.report_type` is `weekly`
- `report.content_json.schema_version` is present
- `report.content_json.sections` contains weekly section ids

## Signal review
```bash
cd /root/.openclaw/workspace/projects/investment
PYTHONPATH=src python3 -m investment_agent.main signal-review
```

Expected:
- `positions` returned
- `research_highlights` returned
- `signals` returned
- at least one signal includes severity/evidence fields

## Test suite
```bash
cd /root/.openclaw/workspace/projects/investment
PYTHONPATH=src python3 -m unittest discover -s tests_python -v
```

Expected:
- all tests pass
