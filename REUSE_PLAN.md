# REUSE_PLAN.md

Source evaluated: `affaan-m/everything-claude-code` @ `da4db99c94cf272d3341910bc8c8a26d2e6e6960`

## Reusable modules

### High value (recommended)
1. `rules/common/security.md`
   - Compact, broadly useful security checklist.
2. `rules/typescript/security.md`
   - Language-specific secret handling baseline for JS/TS.
3. `rules/python/security.md`
   - Language-specific baseline and references.

### Medium value (conditional)
1. `agents/` and selected `skills/`
   - Useful ideas, but behavior/policy assumptions differ from OpenClaw local setup.
   - Needs manual curation and policy alignment.
2. `.opencode/tools/security-audit.ts`
   - Potentially useful scanner logic, but adds runtime/tooling coupling.

### Low value (for this workspace)
1. Bulk localization docs and duplicated variants
   - Good for docs projects, low immediate operational value here.

## Non-recommended modules (this pass)

1. `skills/autonomous-loops/` (and localized variants)
   - Includes remote script piping examples (`curl|bash`) and autonomy patterns not appropriate for conservative integration.
2. `install.sh`, `scripts/`, `commands/` bulk import
   - Too broad; high chance of overlap/duplication with existing OpenClaw workflows.

## Thin adapters required for OpenClaw workspace

1. `ops/ecc/grep-security-scan.sh`
   - Local, dependency-light fallback scanner when `gitleaks/trufflehog/osv-scanner` are missing.
2. `skills/external/ecc/security-rules-reference/README.md`
   - Source attribution and scope guardrails for imported docs.

## Integration policy used

- Integrate only **low-risk, high-value, minimal-change** items.
- Prefer documentation-only imports over executable automation in first pass.
- Keep imports namespaced under `skills/external/ecc` and `ops/ecc` to avoid production path conflicts.