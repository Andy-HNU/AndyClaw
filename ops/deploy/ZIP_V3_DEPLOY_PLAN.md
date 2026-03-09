# ZIP V3 Local Deployment Plan

## Goal
Safely evaluate `openclaw_workspace_package_v3_architecture.zip` against the
current stable workspace before any production deployment or Git inclusion.

## Current Reality
- The running stable workspace is still thin: root governance files plus local ops.
- ZIP v3 introduces a full governed workspace overlay, especially for `investment/`.
- ZIP v3 root files are better aligned with current usage than the default bootstrap files.
- The investment overlay needs role adjustments before deployment:
  Codex should be the primary implementer; OpenClaw should be the tester,
  orchestrator, and runtime operator.

## Non-Goals
- Do not overwrite the running workspace directly.
- Do not commit the raw zip archive.
- Do not expose Codex-only docs into OpenClaw runtime context.

## Proposed Phases

### Phase 1: Static Diff Review
- Compare ZIP root files with current stable workspace root files.
- Classify files into:
  - adopt as-is
  - adopt with edits
  - stage only
  - do not deploy

### Phase 2: Role-Model Rewrite
- Rewrite investment docs that currently imply OpenClaw is a primary developer.
- New target model:
  - Codex implements code, storage, providers, workflows, and tests.
  - OpenClaw calls finished capabilities, executes playbooks, runs acceptance,
    reports failures, and updates project state.

### Phase 3: Local Staging Deployment
- Create a staging workspace copy outside production.
- Deploy only `openclaw_deploy/workspace/`.
- Keep Codex-only docs out of staging runtime root.
- Validate directory structure, root/project split, and file readability.

### Phase 4: Acceptance Review
- Review rewritten docs.
- Check that root governance is stable and project overlays are modular.
- Check that the investment roadmap reflects the new Codex/OpenClaw split.

### Phase 5: Selective Git Inclusion
- Only after staging validation:
  - merge approved root files
  - merge approved project overlays
  - commit structured docs into the repo
- Do not add raw imports, temp bundles, runtime state, or secrets.

## Initial File Classification

### Adopt with edits
- `AGENTS.md`
- `USER.md`
- `SOUL.md`
- `TOOLS.md`
- `IDENTITY.md`
- `MEMORY.md`
- `projects/investment/PROJECT.md`
- `projects/investment/PROFILE.md`
- `projects/investment/RULES.md`
- `projects/investment/agent/AGENT_GUIDE.md`
- `projects/investment/agent/PROJECT_ROADMAP.md`
- `projects/investment/agent/SKILL_ROUTING.md`
- `projects/investment/agent/PLAYBOOK_FULL_SYSTEM.md`

### Likely adopt as-is
- `projects/infra/*`
- `projects/openclaw/*`
- `projects/research/*`
- most `projects/investment/system/*`
- most `projects/investment/tests/*`
- `projects/investment/storage/*`
- `projects/investment/examples/*`

### Stage only for now
- `memory/*`
- `inbox/pending-items.md`
- `projects/investment/src/*`

## Acceptance Criteria
- Root files reflect real collaboration style used today.
- Investment docs clearly assign implementation to Codex.
- OpenClaw is described as runtime executor, tester, and documenter.
- ZIP content can be deployed into staging without polluting runtime with
  Codex-only docs.
- No secrets or runtime state are added to Git.
