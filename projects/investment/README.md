# Investment Project

This directory is the first runnable slice of the investment assistant project.

Current implemented baseline:
- SQLite schema bootstrap
- portfolio-state seeding
- current allocation analysis
- analysis persistence
- AKShare-backed market/news provider baseline with fixture fallback where needed
- provider capability detection for optional external adapters
- price snapshot persistence
- rebalance suggestion/risk-signal persistence
- weekly/monthly review workflows
- stable report schema baseline
- CLI entry points
- unittest coverage for the first slice
- OpenClaw-facing portfolio editing skill and control-surface documentation

Production note:
- `system/portfolio_state.json` can contain test sample holdings in the repo
- real usage may start from `system/portfolio_state.template.json`
- OpenClaw should update holdings through the portfolio editing control flow, not by assuming the sample data is authoritative

Quick start:

```bash
cd /root/.openclaw/workspace/projects/investment
PYTHONPATH=src python3 -m investment_agent.main init-db
PYTHONPATH=src python3 -m investment_agent.main portfolio-summary
PYTHONPATH=src python3 -m investment_agent.main refresh-prices
PYTHONPATH=src python3 -m investment_agent.main provider-capabilities
PYTHONPATH=src python3 -m investment_agent.main signal-review
PYTHONPATH=src python3 -m investment_agent.main weekly-review
PYTHONPATH=src python3 -m investment_agent.main persist-analysis
PYTHONPATH=src python3 -m investment_agent.main persist-rebalance
PYTHONPATH=src python3 -m investment_agent.main monthly-review
PYTHONPATH=src python3 -m unittest discover -s tests_python -v
```
