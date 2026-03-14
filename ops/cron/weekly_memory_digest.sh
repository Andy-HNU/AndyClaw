#!/usr/bin/env bash
set -euo pipefail

export TZ=Asia/Shanghai
WS="/root/.openclaw/workspace"
DB="$WS/memory/memory.db"
ARCHIVE_DIR="$WS/memory/archives"
mkdir -p "$ARCHIVE_DIR"

YEAR="$(date +%G)"
WEEK="$(date +%V)"
STAMP="$(date '+%F %R')"
FILE="$ARCHIVE_DIR/${YEAR}-W${WEEK}.md"

python3 - <<'PY'
import sqlite3, pathlib, json, datetime
ws = pathlib.Path('/root/.openclaw/workspace')
db = ws / 'memory' / 'memory.db'
archive_dir = ws / 'memory' / 'archives'
archive_dir.mkdir(parents=True, exist_ok=True)
now = datetime.datetime.now()
year, week, _ = now.isocalendar()
file = archive_dir / f"{year}-W{week:02d}.md"

conn = sqlite3.connect(db)
cur = conn.cursor()
cur.execute("SELECT category, source, content FROM permanent_memories ORDER BY category, id DESC LIMIT 60")
perms = cur.fetchall()
cur.execute("SELECT source, emotion, content, tags FROM memories WHERE status='fresh' ORDER BY last_reviewed DESC, id DESC LIMIT 40")
fresh = cur.fetchall()
cur.execute("SELECT source, emotion, content, tags FROM memories WHERE status='active' ORDER BY last_reviewed DESC, id DESC LIMIT 40")
active = cur.fetchall()

from collections import defaultdict
by_cat = defaultdict(list)
for c,s,ct in perms:
    by_cat[c or 'misc'].append((s,ct))

def fmt_mem(rows):
    out=[]
    for s,e,c,t in rows:
        tags=''
        try:
            arr=json.loads(t or '[]')
            if arr:
                tags='（tags: ' + '/'.join(str(x) for x in arr[:4]) + '）'
        except Exception:
            pass
        out.append(f"- [{s}/{e}] {c} {tags}".rstrip())
    return out

lines=[]
lines.append('# 🧠 Andy × Claw 结构化记忆')
lines.append(f'> 按遗忘曲线系统整理 · 生成时间：{now:%Y-%m-%d %H:%M}')
lines.append('')
lines.append('---')
lines.append('')
lines.append('## 🔒 永久记忆 (permanent_memories)')
for cat in sorted(by_cat.keys()):
    lines.append(f"\n### category: {cat}")
    for s,ct in by_cat[cat][:12]:
        lines.append(f"- [{s}] {ct}")
lines.append('')
lines.append('## ⏳ 衰减记忆 (memories) — 当前 fresh/active')
lines.append('\n### 🟢 fresh（近1天内）')
lines.extend(fmt_mem(fresh) or ['- （暂无）'])
lines.append('\n### 🟡 active（1~3天内）')
lines.extend(fmt_mem(active) or ['- （暂无）'])
lines.append('')
lines.append('## 📌 项目引用路径（按需维护）')
lines.append('- projects/investment/agent/WORKFLOW_V2.md')
lines.append('- projects/investment/agent/CODEX_TASKS_STABILIZATION.md')
lines.append('- skills/memory-system/')
lines.append('')
lines.append('## 🗒️ 每日开场建议')
lines.append('- 今日待办（task 类永久记忆最多3条）')
lines.append('- 上次在聊（最近1条 fresh）')
lines.append('')
lines.append('## 🗣️ 小咪自身的话（source: self）')
lines.append('- 本周记忆已归档，后续会继续按数据库优先检索。')

file.write_text('\n'.join(lines), encoding='utf-8')

cur.execute("SELECT COUNT(*) FROM permanent_memories")
pc = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM memories WHERE status IN ('fresh','active')")
mc = cur.fetchone()[0]
(ws / 'memory' / '.weekly-counts.txt').write_text(f"{pc},{mc},{file}", encoding='utf-8')
conn.close()
PY

COUNTS="$(cat "$WS/memory/.weekly-counts.txt" 2>/dev/null || echo '0,0,' )"
PC="$(echo "$COUNTS" | cut -d',' -f1)"
MC="$(echo "$COUNTS" | cut -d',' -f2)"
FP="$(echo "$COUNTS" | cut -d',' -f3-)"

/usr/local/bin/openclaw message send \
  --channel telegram \
  --target 8267670204 \
  --message "本周记忆归档已生成，共 ${PC} 条永久记忆、${MC} 条衰减记忆。\n归档：${FP}" >/dev/null 2>&1 || true
