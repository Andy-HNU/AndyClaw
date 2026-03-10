# Investment Phase 1-5 Validation

## Scope
Current runnable slice for the investment project:
- config path discovery
- SQLite schema initialization
- seed current `portfolio_state.json` into SQLite
- current portfolio allocation analysis
- rebalance trigger evaluation
- analysis result persistence
- market data provider abstraction with primary/backup fallback
- price snapshot persistence
- provider capability detection
- rebalance review persistence into suggestions and risk signals
- news provider abstraction with primary/backup fallback
- news item persistence
- monthly investment planning
- monthly report generation and storage
- monthly review workflow
- position/share tracking baseline
- asset-level signal review baseline
- extended CLI
- extended tests

## Implemented Files
- `projects/investment/src/investment_agent/config.py`
- `projects/investment/src/investment_agent/db/repository.py`
- `projects/investment/src/investment_agent/services/portfolio_analyzer.py`
- `projects/investment/src/investment_agent/providers/market_data.py`
- `projects/investment/src/investment_agent/providers/news_data.py`
- `projects/investment/src/investment_agent/providers/factory.py`
- `projects/investment/src/investment_agent/models/portfolio.py`
- `projects/investment/src/investment_agent/main.py`
- `projects/investment/src/investment_agent/services/monthly_planner.py`
- `projects/investment/src/investment_agent/services/rebalance_recorder.py`
- `projects/investment/src/investment_agent/services/report_generator.py`
- `projects/investment/src/investment_agent/services/signal_engine.py`
- `projects/investment/src/investment_agent/workflows/monthly_review.py`
- `projects/investment/tests_python/test_bootstrap.py`

## Commands Run

### Initialize database
```bash
cd /root/.openclaw/workspace/projects/investment
PYTHONPATH=src python3 -m investment_agent.main init-db
```

Result:
- database created at `projects/investment/data/investment.db`
- 10 assets seeded
- latest snapshot written successfully

### Portfolio summary
```bash
cd /root/.openclaw/workspace/projects/investment
PYTHONPATH=src python3 -m investment_agent.main portfolio-summary
```

Result:
- total value: `51653.71`
- current allocation summary generated successfully

### Rebalance check
```bash
cd /root/.openclaw/workspace/projects/investment
PYTHONPATH=src python3 -m investment_agent.main rebalance-check
```

Result:
- current workspace data triggers a rebalance review
- current output identifies:
  - `stock` underweight
  - `gold` overweight
  - `cash` overweight
- priority action: use new funds to repair underweight allocations first

### Refresh prices
```bash
cd /root/.openclaw/workspace/projects/investment
PYTHONPATH=src python3 -m investment_agent.main refresh-prices
```

Result:
- mock primary provider succeeds
- 10 standardized price snapshots inserted into SQLite
- provider fallback path is covered by tests

### Provider capabilities
```bash
cd /root/.openclaw/workspace/projects/investment
PYTHONPATH=src python3 -m investment_agent.main provider-capabilities
```

Result:
- current environment reports `akshare` and `efinance` as unavailable
- local mock primary/backup providers remain enabled
- runtime now exposes why real providers are not yet active

### Persist analysis
```bash
cd /root/.openclaw/workspace/projects/investment
PYTHONPATH=src python3 -m investment_agent.main persist-analysis
```

Result:
- current allocation/deviation snapshot persisted into `analysis_results`
- latest analysis can be read back from SQLite

### Persist rebalance review
```bash
cd /root/.openclaw/workspace/projects/investment
PYTHONPATH=src python3 -m investment_agent.main persist-rebalance
```

Result:
- current rebalance review persisted into `investment_suggestions`
- each breach emitted an `allocation_drift` risk signal
- latest suggestion and open signals can be read back from SQLite

### Monthly plan
```bash
cd /root/.openclaw/workspace/projects/investment
PYTHONPATH=src python3 -m investment_agent.main monthly-plan
```

Result:
- current workspace data returns `needs_repair`
- current allocation vs target:
  - `stock`: `26.5291%` vs target `50%`
  - `bond`: `23.3236%` vs target `25%`
  - `gold`: `26.9156%` vs target `15%`
  - `cash`: `23.2316%` vs target `10%`
- underweight categories are `stock` and `bond`
- gap values used by the planner:
  - `stock`: `12123.59`
  - `bond`: `865.92`
- current `12000` budget is allocated as:
  - `stock`: `11200.04`
  - `bond`: `799.96`
- allocation ratio inside the monthly budget is approximately:
  - `stock`: `93.33%`
  - `bond`: `6.67%`
- `gold` and `cash` receive `0` new budget in the current plan because both are already above target allocation

### Monthly review
```bash
cd /root/.openclaw/workspace/projects/investment
PYTHONPATH=src python3 -m investment_agent.main monthly-review
```

Result:
- price refresh succeeded with `mock-primary`
- news refresh succeeded with `mock-news-primary`
- current workflow persisted:
  - price snapshots
  - news items
  - analysis result
  - rebalance review
  - monthly report
- monthly report title is `2026-03 投资月报`
- report payload includes:
  - portfolio summary
  - detailed position changes
  - asset research highlights
  - rebalance result
  - monthly investment plan
  - risk summary
  - news observations
  - next-month watchlist

### Signal review
```bash
cd /root/.openclaw/workspace/projects/investment
PYTHONPATH=src python3 -m investment_agent.main signal-review
```

Result:
- current portfolio state now includes `shares` and `average_cost`
- review returns:
  - detailed position changes
  - estimated price-driven vs flow-driven changes
  - asset research highlights
  - asset-level signals such as:
    - `suspected_distribution`
    - `valuation_premium_warning`
    - `risk_adjusted_return_deterioration`
    - `manager_style_drift`

### Tests
```bash
cd /root/.openclaw/workspace/projects/investment
PYTHONPATH=src python3 -m unittest discover -s tests_python -v
```

Result:
- 21 tests passed

## Notes
- The spec-style ratio test uses synthetic data from the test doc, not the
  current workspace portfolio file. This keeps the ratio formula test stable.
- The current workspace portfolio summary test checks live project data and
  confirms category coverage and total consistency.
- The current provider implementation is intentionally local and deterministic:
  it validates the abstraction, fallback path, and storage flow before any
  external market-data adapter is added.
- The current environment does not have `akshare` or `efinance` installed, so
  capability detection reports them as unavailable instead of silently failing
  at runtime.
- The current monthly-review workflow is runnable and validated locally, but
  it still depends on deterministic mock market/news inputs rather than real
  upstream adapters.
- The current V2 batch-1 signal layer uses deterministic local research
  fixtures. This keeps test outputs stable while avoiding premature direct
  dependency on external trading repos.
- Current phase naming is now broader than the original document title: the
  validation covers the early reporting/workflow baseline in addition to the
  original phase-1 to phase-3 implementation slice.

## Next Rollout Target
- implement a real adapter behind the `market_data_provider` abstraction
- implement a real adapter behind the `news_data_provider` abstraction
- prepare a wider OpenClaw runtime acceptance and replay flow
- commit the monthly review baseline as the next formal phase checkpoint
