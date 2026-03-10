# Implementation Status

## Date
2026-03-11

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
- first real external adapter baseline now uses AKShare for ETF/open-fund prices, Shanghai Gold Exchange spot gold, and keyword news, with fixture fallback kept only for cash-like assets
- weekly review workflow is now implemented and persists `weekly` reports
- report schema baseline is now documented and stabilized around `schema_version` and `sections`
- OpenClaw playbooks are now aligned with the real CLI surface for daily, weekly, and monthly review
- screenshot import baseline is now implemented with a vision-first entry point and local OCR fallback
- OpenClaw now has dedicated runtime-facing skill surfaces for portfolio editing, research editing, and screenshot import
- Telegram daily capture flow is now documented as a transport-layer integration path into `import-snapshot`
- local validation currently passes with `31` Python tests

## In Progress
- move from mock-only market/news provider execution toward real external adapters
- keep validation docs and OpenClaw acceptance commands aligned with the expanded CLI surface
- decide whether the monthly-review baseline should be committed as the next formal phase checkpoint
- keep the vision client optional so local OCR remains a deterministic fallback path

## Next Steps
1. decide whether to replace the remaining cash-like fixture path with a more explicit non-market cash model
2. evaluate whether `efinance` is still worth keeping as a secondary real provider path
3. extend report schema stability from the current baseline into more formal consumer contracts
4. expand OpenClaw runtime acceptance from command-level checks into reusable replay scripts
5. connect future Telegram reminder / attachment delivery to the new `import-snapshot` entry point

## Do Not Forget
- do not import ZIP runtime memory/inbox content into production blindly
- do not commit secrets, runtime state, or raw import bundles
- keep production OpenClaw workspace stable while staging evolves
