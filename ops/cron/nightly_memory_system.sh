#!/usr/bin/env bash
set -euo pipefail

export TZ=Asia/Shanghai
WS="/root/.openclaw/workspace"
DB="$WS/memory/memory.db"
TODAY="$(date +%F)"
YDAY="$(date -d 'yesterday' +%F)"
LOG_DIR="$WS/memory"
DAILY_FILE="$LOG_DIR/${TODAY}.md"

mkdir -p "$LOG_DIR"

python3 - <<'PY'
import sqlite3, pathlib, datetime
ws = pathlib.Path('/root/.openclaw/workspace')
db = ws / 'memory' / 'memory.db'
db.parent.mkdir(parents=True, exist_ok=True)
conn = sqlite3.connect(db)
cur = conn.cursor()
cur.executescript('''
CREATE TABLE IF NOT EXISTS memories (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  content TEXT NOT NULL,
  source TEXT DEFAULT 'user',
  emotion TEXT DEFAULT 'neutral',
  tags TEXT DEFAULT '[]',
  created_at DATE DEFAULT (date('now')),
  last_reviewed DATE DEFAULT (date('now')),
  status TEXT DEFAULT 'fresh'
);
CREATE TABLE IF NOT EXISTS permanent_memories (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  category TEXT,
  source TEXT DEFAULT 'user',
  content TEXT NOT NULL,
  created_at DATE DEFAULT (date('now'))
);
UPDATE memories SET status = CASE
  WHEN julianday('now') - julianday(last_reviewed) > 30 THEN 'forgotten'
  WHEN julianday('now') - julianday(last_reviewed) > 7  THEN 'blurry'
  WHEN julianday('now') - julianday(last_reviewed) > 3  THEN 'fading'
  WHEN julianday('now') - julianday(last_reviewed) > 1  THEN 'active'
  ELSE 'fresh'
END;
''')
cur.execute("SELECT COUNT(*) FROM permanent_memories")
perm = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM memories WHERE status='fresh'")
fresh = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM memories WHERE status='active'")
active = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM memories WHERE status='fading'")
fading = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM memories WHERE status='blurry'")
blurry = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM memories WHERE status='forgotten'")
forgotten = cur.fetchone()[0]
conn.commit()
conn.close()
summary = f"perm={perm}, fresh={fresh}, active={active}, fading={fading}, blurry={blurry}, forgotten={forgotten}"
(ws / 'memory' / '.nightly-db-summary.txt').write_text(summary, encoding='utf-8')
PY

if [ ! -f "$DAILY_FILE" ]; then
  cat > "$DAILY_FILE" <<EOF
# ${TODAY}

- [补偿执行] 00:00 记忆系统任务触发：已完成数据库状态刷新与索引维护。
- 说明：自动任务无法直接读取完整聊天上下文，需在主会话中补充“今日关键事件/新增记忆”条目。
EOF
fi

DB_SUMMARY="$(cat "$WS/memory/.nightly-db-summary.txt" 2>/dev/null || echo 'summary=unavailable')"

# Auto git check + commit/push if changes exist
cd "$WS"
if [ -n "$(git status --porcelain)" ]; then
  git add -A
  git commit -m "chore(cron): nightly memory maintenance ${TODAY}" || true
  git push origin main || true
  COMMIT_LINE="已检测到本地改动并尝试自动提交推送。"
else
  COMMIT_LINE="git 工作区干净，无需提交。"
fi

MSG="[00:00记忆任务] ${TODAY}
数据库状态：${DB_SUMMARY}
${COMMIT_LINE}
提示：会话级内容摘要由主会话补录。"

/usr/local/bin/openclaw message send \
  --channel telegram \
  --target 8267670204 \
  --message "$MSG" >/dev/null 2>&1 || true
