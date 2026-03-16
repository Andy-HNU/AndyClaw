#!/usr/bin/env bash
set -euo pipefail

# Weekly reminder to review reserve-skill upgrades (AReaL/ontology gate)
/usr/local/bin/openclaw message send \
  --channel telegram \
  --target 8267670204 \
  --message "每周系统升级检查时间到：请评估储备技能（如 AReaL）是否满足启用条件。\n规则：即使命中条件，也先报告并等待你确认，未确认不安装不切换。" >/dev/null 2>&1 || true
