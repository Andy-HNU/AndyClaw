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
- first real external market/news adapter baseline
- weekly review workflow baseline
- stable report schema baseline
- screenshot import baseline with vision-first orchestration and OCR fallback
- daily review workflow baseline
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
- `projects/investment/src/investment_agent/services/ocr_importer.py`
- `projects/investment/src/investment_agent/services/snapshot_importer.py`
- `projects/investment/src/investment_agent/workflows/weekly_review.py`
- `projects/investment/src/investment_agent/workflows/daily_review.py`
- `projects/investment/src/investment_agent/workflows/monthly_review.py`
- `projects/investment/tests_python/test_bootstrap.py`
- `projects/investment/storage/REPORT_SCHEMA.md`

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
- AKShare hybrid primary provider succeeds
- 10 standardized price snapshots inserted into SQLite
- ETF, open-fund, and `黄金` assets use live AKShare / SGE data
- `现金` remains on local fixture quotes inside the primary provider
- provider fallback path is still covered by tests

### Provider capabilities
```bash
cd /root/.openclaw/workspace/projects/investment
PYTHONPATH=src python3 -m investment_agent.main provider-capabilities
```

Result:
- current environment reports `akshare-market` and `akshare-news` as enabled
- `efinance` remains unavailable
- local mock providers remain enabled as controlled backup sources

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
- price refresh succeeded with `akshare-market`
- news refresh succeeded with `akshare-news`
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

### Daily review
```bash
cd /root/.openclaw/workspace/projects/investment
PYTHONPATH=src python3 -m investment_agent.main daily-review
```

Result:
- daily workflow refreshes prices and news
- daily workflow evaluates current rebalance status
- daily workflow persists a `daily` report into `reports`
- daily report currently includes:
  - `portfolio_snapshot`
  - `rebalance_review`
  - `risk_summary`
  - `news_summary`
  - `action_items`
- current sample output includes same-day action guidance based on:
  - current allocation deviation
  - open signal set
  - top fetched news items

### Weekly review
```bash
cd /root/.openclaw/workspace/projects/investment
PYTHONPATH=src python3 -m investment_agent.main weekly-review
```

Result:
- weekly workflow refreshes prices and news
- weekly report is persisted into `reports`
- report schema includes:
  - `schema_version`
  - `summary`
  - `sections`
- weekly sections include:
  - `portfolio_snapshot`
  - `position_changes`
  - `risk_summary`
  - `news_summary`
  - `watchlist`

### Snapshot import
```bash
cd /root/.openclaw/workspace/projects/investment
PYTHONPATH=src python3 -m investment_agent.main import-snapshot --portfolio-image /root/usrFile/bb560d57ad2761440ddc9b4069e96e83.jpg --gold-image /root/usrFile/a9c549ccf141b31d97cd81b79aa2f98c.jpg
```

Result:
- current environment falls back to local OCR because no vision client is configured
- the import still returns a structured candidate payload with:
  - holdings overview total value: `35805.93`
  - cash value: `9938.51`
  - gold total value: `14077.33`
  - gold shares: `12.1713`
- merged candidate portfolio total is `49883.26`
- output records:
  - `source = ocr-fallback`
  - `fallback_used = true`
  - `fallback_reason = vision client unavailable`
- the intended next step is to route the candidate through `portfolio_editor`

### Tests
```bash
cd /root/.openclaw/workspace/projects/investment
PYTHONPATH=src python3 -m unittest discover -s tests_python -v
```

Result:
- 33 tests passed

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
  it now uses real AKShare adapters for ETF/open-fund price refresh and
  keyword news collection, plus real SGE gold pricing, with local fixtures
  kept only for unsupported cash-like assets.
- The current V2 batch-1 signal layer uses deterministic local research
  fixtures. This keeps test outputs stable while avoiding premature direct
  dependency on external trading repos.
- The current snapshot import path is deliberately layered: model vision is
  preferred when configured, but local OCR remains the stable fallback so
  OpenClaw can still operate without online vision dependencies.
- The current daily/weekly/monthly workflow split should be treated as basic
  infrastructure only; higher-order recurring task composition is intentionally
  left to OpenClaw's natural-language runtime layer.
- The current report schema is stable enough for OpenClaw/runtime consumption,
  but should still be treated as a baseline rather than a frozen public API.
- Current phase naming is now broader than the original document title: the
  validation covers the early reporting/workflow baseline in addition to the
  original phase-1 to phase-3 implementation slice.

## Next Rollout Target
- decide whether to keep `cash` on the current explicit local fixture model
- prepare a wider OpenClaw runtime acceptance and replay flow
- promote the current weekly/monthly report schema baseline into a more formal contract
- commit the current real-provider + weekly/monthly workflow baseline as the next formal phase checkpoint
