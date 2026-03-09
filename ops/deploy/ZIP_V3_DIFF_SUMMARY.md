# ZIP V3 Diff Summary

## Stable Workspace vs ZIP V3

### Current stable workspace
- minimal root governance files
- local ops assets
- no committed `projects/` overlays yet
- no committed `memory/` or `inbox/` structures

### ZIP v3
- replaces the default bootstrap-style root with governed long-term root files
- introduces project overlays:
  - `investment`
  - `infra`
  - `openclaw`
  - `research`
- introduces `memory/` and `inbox/` structure
- introduces an investment project architecture that is much closer to a real build plan

## Key Finding
ZIP v3 is directionally correct for governance and project structure, but the
investment overlay needed a role-model rewrite after real usage feedback:
- Codex should be the primary builder
- OpenClaw should be the primary runtime operator, tester, and acceptance layer

## Staging Rewrites Already Applied
- `AGENTS.md`
- `projects/investment/PROJECT.md`
- `projects/investment/PROFILE.md`
- `projects/investment/RULES.md`
- `projects/investment/agent/AGENT_GUIDE.md`
- `projects/investment/agent/PROJECT_ROADMAP.md`

## Recommended Local Deployment Order
1. adopt rewritten root governance files into staging
2. deploy `projects/infra`, `projects/openclaw`, `projects/research` as-is
3. deploy rewritten `projects/investment`
4. stage `memory/` and `inbox/`, but do not auto-merge current runtime content
5. validate structure and runtime visibility rules
6. only then selectively commit the approved files into Git

## Do Not Deploy Directly Yet
- raw `memory/*` contents from ZIP
- raw `inbox/pending-items.md`
- raw zip archive
- Codex-only deployment docs

## Next Review Targets
- `projects/investment/agent/SKILL_ROUTING.md`
- `projects/investment/agent/PLAYBOOK_FULL_SYSTEM.md`
- `projects/investment/examples/example_dialogues.md`
- root `MEMORY.md` introduction into the current stable workspace
