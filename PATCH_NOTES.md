# PATCH_NOTES.md

Upstream repository: `https://github.com/affaan-m/everything-claude-code`

Upstream commit used: `da4db99c94cf272d3341910bc8c8a26d2e6e6960`

## What was copied

Copied (documentation-only subset):
- `rules/common/security.md` -> `skills/external/ecc/security-rules-reference/common-security.md`
- `rules/typescript/security.md` -> `skills/external/ecc/security-rules-reference/typescript-security.md`
- `rules/python/security.md` -> `skills/external/ecc/security-rules-reference/python-security.md`

Added integration metadata:
- `skills/external/ecc/security-rules-reference/README.md`

Added thin local adapter:
- `ops/ecc/grep-security-scan.sh`

## What was modified

- File names were adjusted to avoid collisions and make imported scope explicit (`*-security.md`).
- Added README attribution and explicit exclusion scope.
- Implemented local fallback scanner script for environments lacking `gitleaks/trufflehog/rg`.

## Why this is safe

- Imported content is markdown-only (non-executable references).
- No upstream executables/installers/hooks were integrated.
- Risky modules (autonomy installers / broad scripts) were intentionally excluded.
- New script is local, transparent shell logic with no network execution.

## Backups / overwrite policy

- No existing production scripts were overwritten.
- All additions are new namespaced paths under:
  - `skills/external/ecc/`
  - `ops/ecc/`
## Phase-2 additions (docs/rules/templates only)

Copied (documentation-only subset):
- `rules/common/coding-style.md` -> `skills/external/ecc/phase2/rules-common/common-coding-style.md`
- `rules/common/development-workflow.md` -> `skills/external/ecc/phase2/rules-common/common-development-workflow.md`
- `rules/common/git-workflow.md` -> `skills/external/ecc/phase2/rules-common/common-git-workflow.md`
- `rules/common/patterns.md` -> `skills/external/ecc/phase2/rules-common/common-patterns.md`
- `rules/common/testing.md` -> `skills/external/ecc/phase2/rules-common/common-testing.md`
- `rules/README.md` -> `skills/external/ecc/phase2/rules-overview.md`

Added local glue/guardrails:
- `skills/external/ecc/phase2/README.md`
- `skills/external/ecc/phase2/SAFE_ADOPTION_GUIDE.md`
- `CAPABILITY_DELTA.md`

Safety notes:
- Re-audited selected candidate files before import (no dangerous-pattern hits).
- No executable files added in phase-2.
- Scripts/installers/hooks/autonomous-loop guidance intentionally excluded.
