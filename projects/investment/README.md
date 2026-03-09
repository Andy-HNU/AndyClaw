# Investment Project

This directory is the first runnable slice of the investment assistant project.

Current implemented baseline:
- SQLite schema bootstrap
- portfolio-state seeding
- current allocation analysis
- analysis persistence
- mock market-data provider baseline with primary/backup fallback
- provider capability detection for optional external adapters
- price snapshot persistence
- rebalance suggestion/risk-signal persistence
- CLI entry points
- unittest coverage for the first slice

Quick start:

```bash
cd /root/.openclaw/workspace/projects/investment
PYTHONPATH=src python3 -m investment_agent.main init-db
PYTHONPATH=src python3 -m investment_agent.main portfolio-summary
PYTHONPATH=src python3 -m investment_agent.main refresh-prices
PYTHONPATH=src python3 -m investment_agent.main provider-capabilities
PYTHONPATH=src python3 -m investment_agent.main persist-analysis
PYTHONPATH=src python3 -m investment_agent.main persist-rebalance
PYTHONPATH=src python3 -m unittest discover -s tests_python -v
```
