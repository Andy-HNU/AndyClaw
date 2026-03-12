# SAFE_ADOPTION_GUIDE

Use this guide to apply ECC phase-2 references safely.

## 1) Decide applicability first

Before using a rule, confirm:
- It is relevant to the current task type (coding style vs testing vs git process).
- It does not conflict with local OpenClaw policies or repo conventions.
- It does not introduce implicit automation behavior.

## 2) Use as prompts/checklists, not executable instructions

Recommended workflow:
1. Pick one relevant rule doc.
2. Extract 3-5 checklist items for the current task.
3. Apply them manually.
4. Record deviations in PR/task notes when needed.

## 3) Conflict resolution order

If guidance conflicts:
1. System/developer safety instructions
2. Workspace-local policy/docs
3. ECC imported references (this folder)
4. Upstream examples or community snippets

## 4) Red flags requiring stop-and-review

Do not proceed without review if you encounter:
- Remote script piping (e.g., `curl ... | bash`)
- Silent auto-execution hooks
- Autonomous loop behavior without explicit oversight
- Commands that alter host security posture unexpectedly

## 5) Suggested practical use

- `common-coding-style.md`: pre-merge readability/quality checks
- `common-testing.md`: test strategy and coverage gating reminders
- `common-git-workflow.md`: commit/PR hygiene checklist
- `common-development-workflow.md`: planning-to-review process outline
- `common-patterns.md`: architecture pattern prompts
