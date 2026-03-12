#!/usr/bin/env bash
set -euo pipefail

/usr/local/bin/openclaw message send \
  --channel telegram \
  --target 8267670204 \
  --message "提醒一下：到点啦，发我今日仓位两张图（黄金页 + 基金总仓页）📸" >/dev/null 2>&1
