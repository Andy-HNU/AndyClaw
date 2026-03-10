# Implementation Status

## Date
2026-03-10

## Objective
Drive the investment project from document-only planning toward a Codex-led
implementation pipeline, while keeping OpenClaw as the runtime operator,
tester, and acceptance layer.

## Decisions Locked In
- The Git repo at `/root/.openclaw/workspace` is now the source of truth.
- ZIP v3 should not be deployed raw into the production workspace.
- ZIP v3 should first be rewritten and validated in local staging.
- Codex is the default implementation owner for code, schema, providers,
  services, workflows, and tests.
- OpenClaw is the default owner for runtime invocation, playbook execution,
  acceptance checks, and project-state updates.

## Current State
- staging copy exists at `staging/zip_v3/`
- root/project deployment and rewrite plans are documented in `ops/deploy/`
- key investment docs in staging have already been rewritten
- repo is initialized and pushed to GitHub
- first runnable investment slice is merged into `projects/investment`
- market-data mock provider baseline, fallback logic, and SQLite persistence are now implemented
- provider capability detection is now implemented for `akshare` / `efinance`
- rebalance reviews now persist into `investment_suggestions` and `risk_signals`
- local news-ingestion baseline is now implemented with primary/backup fallback
- monthly investment planning is now implemented behind the current analysis output
- monthly review workflow now chains price refresh, news refresh, analysis, rebalance persistence, and report storage
- monthly reports now persist into `reports` with markdown and JSON payloads
- CLI surface now includes `monthly-plan` and `monthly-review`
- V2 batch-1 baseline now includes position/share tracking, asset research fixtures, and asset-level signal review
- CLI surface now also includes `signal-review` for direct inspection of V2 signals
- first real external adapter baseline now uses AKShare for ETF/open-fund prices and keyword news, with fixture fallback for unsupported assets like cash/gold
- local validation currently passes with `24` Python tests

## In Progress
- move from mock-only market/news provider execution toward real external adapters
- keep validation docs and OpenClaw acceptance commands aligned with the expanded CLI surface
- decide whether the monthly-review baseline should be committed as the next formal phase checkpoint

## Next Steps
1. decide whether to replace the current AKShare+fixture hybrid with broader real coverage for gold/cash-like assets
2. expand OpenClaw acceptance playbooks for refresh -> analysis -> monthly-review flow
3. decide whether to split report generation / workflow outputs into more stable user-facing schemas
4. evaluate whether `efinance` is still worth keeping as a secondary real provider path
5. record the current phase-1 to phase-5 baseline as a formal committed checkpoint

## Do Not Forget
- do not import ZIP runtime memory/inbox content into production blindly
- do not commit secrets, runtime state, or raw import bundles
- keep production OpenClaw workspace stable while staging evolves
