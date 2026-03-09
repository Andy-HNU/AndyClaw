# OpenClaw Acceptance Commands

Use these commands when OpenClaw or Codex needs to verify the first investment
implementation slice.

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

## Test suite
```bash
cd /root/.openclaw/workspace/projects/investment
PYTHONPATH=src python3 -m unittest discover -s tests_python -v
```

Expected:
- all tests pass
