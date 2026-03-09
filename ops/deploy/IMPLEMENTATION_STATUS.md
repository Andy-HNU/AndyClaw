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

## In Progress
- finish the remaining investment staging rewrites
- scaffold the first runnable code slice under the repo
- implement SQLite baseline and first verification loop

## Next Steps
1. rewrite remaining investment docs:
   - `agent/SKILL_ROUTING.md`
   - `agent/PLAYBOOK_FULL_SYSTEM.md`
   - `examples/example_dialogues.md`
2. create repo-side project structure for `projects/investment/src/`
3. implement SQLite schema/config/repository baseline
4. add tests for the first slice
5. record deployment and validation results

## Do Not Forget
- do not import ZIP runtime memory/inbox content into production blindly
- do not commit secrets, runtime state, or raw import bundles
- keep production OpenClaw workspace stable while staging evolves
