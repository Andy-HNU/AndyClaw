# ZIP V3 Rewrite Points

## Why Rewrite
Actual usage shows OpenClaw is not the strongest primary coding agent for this
system. The operating model should be:
- Codex: primary builder
- OpenClaw: primary runtime operator, tester, and acceptance layer

## Required Rewrites

### Root files
- `AGENTS.md`
  Add explicit rule that project implementation tasks default to Codex when
  code, refactors, database design, or service wiring are required.
- `TOOLS.md`
  Emphasize that high-risk or multi-file implementation changes should be
  prepared for Codex execution.
- `MEMORY.md`
  No structural rewrite needed, but deployment should consider it a new root
  baseline because current stable workspace lacks this file.

### Investment project
- `PROJECT.md`
  Replace “OpenClaw 与 Codex 持续开发” with “Codex 主导开发实现，OpenClaw 主导运行调用、测试验收与状态沉淀”.
- `PROFILE.md`
  Replace “如何被 OpenClaw 内化为能力” with “如何被 Codex 实现并被 OpenClaw 稳定调用”.
- `RULES.md`
  Update rule 7 so new rules are proposed by OpenClaw but implemented or
  integrated through Codex when code or schema changes are involved.
- `agent/AGENT_GUIDE.md`
  Replace “若已有代码能力，则调用代码；若尚未实现，则按 skill 定义输出开发任务”
  with a stronger split:
  - implemented capability -> OpenClaw can call
  - missing capability -> generate Codex task package
- `agent/PROJECT_ROADMAP.md`
  Each build phase should explicitly say “implemented by Codex”.
  Final phase should focus on OpenClaw operationalization and acceptance.
- `agent/SKILL_ROUTING.md`
  Clarify that skill routing is for using finished capabilities, not implying
  OpenClaw will author the implementation itself.
- `agent/PLAYBOOK_FULL_SYSTEM.md`
  Clarify which steps are runtime operations versus implementation tasks.

## Optional Rewrites
- `examples/example_dialogues.md`
  Keep the user-facing behavior, but ensure underlying assumption is that the
  called capabilities already exist.
- `agent/GITHUB_SKILL_DISCOVERY.md`
  Keep mostly as-is, but bias GitHub reference collection toward Codex-led
  implementation work.
