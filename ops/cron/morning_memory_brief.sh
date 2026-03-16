#!/usr/bin/env bash
set -euo pipefail

export TZ=Asia/Shanghai
WS="/root/.openclaw/workspace"
YDAY="$(date -d 'yesterday' +%F)"
FILE="$WS/memory/${YDAY}.md"

if [ -f "$FILE" ]; then
  SUMMARY="$(python3 - <<'PY'
from pathlib import Path
import datetime
p=Path('/root/.openclaw/workspace/memory') / (datetime.datetime.now()-datetime.timedelta(days=1)).strftime('%Y-%m-%d.md')
text=p.read_text(encoding='utf-8',errors='ignore').splitlines()
items=[ln.strip() for ln in text if ln.strip().startswith('- ')]
if not items:
    print('昨天无结构化条目。')
else:
    print('\\n'.join(items[:6]))
PY
)"
else
  SUMMARY="未找到昨日日志文件：memory/${YDAY}.md"
fi

MSG="早安 Andy ☀️
昨日记忆简报（${YDAY}）：
${SUMMARY}

提醒：如当前会话上下文较高，请你手动执行一次 compact。"

/usr/local/bin/openclaw message send \
  --channel telegram \
  --target 8267670204 \
  --message "$MSG" >/dev/null 2>&1 || true
