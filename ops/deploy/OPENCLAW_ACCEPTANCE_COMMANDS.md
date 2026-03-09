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

## Provider capabilities
```bash
cd /root/.openclaw/workspace/projects/investment
PYTHONPATH=src python3 -m investment_agent.main provider-capabilities
```

Expected:
- provider list returned
- unavailable real providers explain why they are disabled
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

## Test suite
```bash
cd /root/.openclaw/workspace/projects/investment
PYTHONPATH=src python3 -m unittest discover -s tests_python -v
```

Expected:
- all tests pass
