#!/usr/bin/env bash
set -euo pipefail

# Optional random delay (seconds), default 0
JITTER_SEC="${1:-0}"
if [[ "$JITTER_SEC" =~ ^[0-9]+$ ]] && [[ "$JITTER_SEC" -gt 0 ]]; then
  sleep "$((RANDOM % JITTER_SEC))"
fi

OUT="$(python3 - <<'PY'
import requests, urllib.parse, xml.etree.ElementTree as ET, random

queries=[
  'odd science news',
  'weird tech news',
  'formula 1 latest news',
  'iran hormuz latest',
  'ai product launch today'
]
q=random.choice(queries)
url='https://news.google.com/rss/search?q='+urllib.parse.quote(q)+'&hl=en-US&gl=US&ceid=US:en'
text='今日冲浪：暂时没抓到像样的，稍后再来一轮。'
try:
    r=requests.get(url,timeout=15,headers={'User-Agent':'Mozilla/5.0'})
    root=ET.fromstring(r.text)
    items=root.findall('.//item')[:3]
    if items:
        lines=['今日冲浪播报（随机时段）🌊']
        for i,it in enumerate(items,1):
            title=(it.findtext('title') or '').strip()
            link=(it.findtext('link') or '').strip()
            lines.append(f'{i}. {title}\n{link}')
        text='\n\n'.join(lines)
except Exception:
    pass
print(text)
PY
)"

/usr/local/bin/openclaw message send \
  --channel telegram \
  --target 8267670204 \
  --message "$OUT" >/dev/null 2>&1
