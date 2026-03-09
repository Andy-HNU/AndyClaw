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

## In Progress
- extend the investment codebase beyond bootstrap into reusable provider/service layers
- keep validation docs and OpenClaw acceptance commands aligned with the real CLI surface

## Next Steps
1. implement a real `market_data_provider` adapter behind the current abstraction
2. persist rebalance outputs into `investment_suggestions` or `risk_signals`
3. add news ingestion baseline and related tests
4. expand OpenClaw acceptance playbooks for refresh -> analysis -> rebalance flow
5. record phase-2 validation and keep project status current

## Do Not Forget
- do not import ZIP runtime memory/inbox content into production blindly
- do not commit secrets, runtime state, or raw import bundles
- keep production OpenClaw workspace stable while staging evolves
