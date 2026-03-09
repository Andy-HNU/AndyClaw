# Investment Project

This directory is the first runnable slice of the investment assistant project.

Current implemented baseline:
- SQLite schema bootstrap
- portfolio-state seeding
- current allocation analysis
- CLI entry points
- unittest coverage for the first slice

Quick start:

```bash
cd /root/.openclaw/workspace/projects/investment
PYTHONPATH=src python3 -m investment_agent.main init-db
PYTHONPATH=src python3 -m investment_agent.main portfolio-summary
PYTHONPATH=src python3 -m unittest discover -s tests_python -v
```
