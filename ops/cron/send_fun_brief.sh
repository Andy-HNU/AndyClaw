#!/usr/bin/env bash
set -euo pipefail

OUT="$(python3 - <<'PY'
import requests, urllib.parse, xml.etree.ElementTree as ET, random

topics=[
    'odd science news',
    'weird tech news',
    'funny world news',
]
q=random.choice(topics)
url='https://news.google.com/rss/search?q='+urllib.parse.quote(q)+'&hl=en-US&gl=US&ceid=US:en'
line='今天没抓到离谱新闻，先欠你一条，明天补上。'
try:
    r=requests.get(url,timeout=15,headers={'User-Agent':'Mozilla/5.0'})
    root=ET.fromstring(r.text)
    item=root.find('.//item')
    if item is not None:
        title=(item.findtext('title') or '').strip()
        link=(item.findtext('link') or '').strip()
        line=f'《今日离谱但真实》\n- {title}\n{link}'
except Exception:
    pass

meme=''
try:
    m=requests.get('https://meme-api.com/gimme',timeout=10).json()
    meme_url=(m.get('url') or '').strip()
    if meme_url:
        meme='\n\n今日meme：'+meme_url
except Exception:
    pass

print(line+meme)
PY
)"

/usr/local/bin/openclaw message send \
  --channel telegram \
  --target 8267670204 \
  --message "$OUT" >/dev/null 2>&1
