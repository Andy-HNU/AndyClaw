# CAPABILITY_DELTA.md

## Scope
Comparison of practical workspace capability **before vs after ECC phase-2** imports.

## Before (after phase-1 only)

Available from ECC:
- Security-specific references (common/python/typescript security).

Practical limitations:
- Weak guidance on end-to-end dev workflow (plan -> test -> review -> commit).
- No reusable baseline for coding style consistency.
- Limited shared checklist for testing discipline and PR/commit hygiene.
- Architecture/pattern prompts were fragmented.

## After (phase-2 applied)

New docs-only capabilities added:
- `common-development-workflow`: repeatable implementation flow guidance.
- `common-testing`: stronger TDD and coverage checklist baseline.
- `common-git-workflow`: cleaner commit/PR process consistency.
- `common-coding-style`: quality and immutability-oriented style reminders.
- `common-patterns`: reusable architecture/design prompts.
- `rules-overview`: map of common-vs-language layering model.

## Practical improvements

1. **Higher delivery consistency**
   - Teams can follow a shared lightweight process without importing automation.
2. **Better review quality**
   - Clearer pre-merge checks (style, tests, workflow, git hygiene).
3. **Faster onboarding**
   - New contributors get compact reference set under one namespace.
4. **Safer reuse posture**
   - No executable imports; guidance is intentionally checklist/reference only.
5. **Lower integration risk**
   - Excluded scripts/hooks/installers/autonomous-loop patterns by policy.

## Net effect

Phase-2 increases day-to-day engineering guidance breadth (workflow/testing/style/patterns/git) while preserving the same security posture as phase-1: **docs-only, non-executable, explicitly gated imports**.
