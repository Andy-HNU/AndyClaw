# ECC Phase-2 Safe Imports (Docs-Only)

Source: `affaan-m/everything-claude-code` @ `da4db99c94cf272d3341910bc8c8a26d2e6e6960` (MIT)
Imported on: 2026-03-12 (Asia/Shanghai)

## Scope

This phase imports **non-executable, high-value rule/reference docs** only.

Included:
- `rules-overview.md`
- `rules-common/common-coding-style.md`
- `rules-common/common-development-workflow.md`
- `rules-common/common-git-workflow.md`
- `rules-common/common-patterns.md`
- `rules-common/common-testing.md`

## Security Exclusions (explicit)

Not imported in phase-2:
- Scripts/installers/hooks that execute commands
- Autonomous-loop modules and self-driving workflows
- Any `curl|bash` or remote script piping guidance
- Executable assets, binary tooling, or CI automation payloads

## Usage in this workspace

Treat these files as **reference checklists**, not blind policy.
- Prefer OpenClaw system/developer safety rules when conflicts exist.
- Apply selectively per task and environment.
- Do not copy execution snippets into automation without local review.

See `SAFE_ADOPTION_GUIDE.md` for practical integration steps.
