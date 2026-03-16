#!/usr/bin/env python3
import argparse
import json
import sqlite3
from pathlib import Path

"""
Input JSON shape:
{
  "domain_knowledge": [{"domain":"energy","topic":"x","content":"...","key_numbers": {...}}],
  "historical_reference": [{"event_type":"oil_crisis","year":2022,"description":"...","outcome":"...","analogy_power":4}],
  "current_state": [{"category":"macro","key":"fed_rate","value":"5.25-5.5%","context":"...","valid_until":"2026-12-31"}]
}
"""

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--db', default='memory/policy_knowledge.db')
    p.add_argument('--input', required=True, help='JSON file path')
    args = p.parse_args()

    payload = json.loads(Path(args.input).read_text(encoding='utf-8'))
    conn = sqlite3.connect(args.db)
    cur = conn.cursor()

    for r in payload.get('domain_knowledge', []):
        cur.execute('''
            INSERT INTO domain_knowledge(domain, topic, content, key_numbers, updated_at)
            VALUES(?,?,?,?,date('now'))
            ON CONFLICT(domain, topic) DO UPDATE SET
              content=excluded.content,
              key_numbers=excluded.key_numbers,
              updated_at=date('now')
        ''', (r['domain'], r['topic'], r['content'], json.dumps(r.get('key_numbers', {}), ensure_ascii=False)))

    for r in payload.get('historical_reference', []):
        cur.execute('''
            INSERT OR IGNORE INTO historical_reference(event_type, year, description, outcome, analogy_power)
            VALUES(?,?,?,?,?)
        ''', (r['event_type'], int(r['year']), r['description'], r.get('outcome'), r.get('analogy_power')))

    for r in payload.get('current_state', []):
        cur.execute('''
            INSERT INTO current_state(category, key, value, context, valid_until)
            VALUES(?,?,?,?,?)
            ON CONFLICT(category, key) DO UPDATE SET
              value=excluded.value,
              context=excluded.context,
              valid_until=excluded.valid_until
        ''', (r['category'], r['key'], str(r['value']), r.get('context'), r.get('valid_until')))

    conn.commit()

    stats = {}
    for t in ('domain_knowledge', 'historical_reference', 'current_state'):
        cur.execute(f'SELECT COUNT(*) FROM {t}')
        stats[t] = cur.fetchone()[0]
    conn.close()
    print(json.dumps({'status': 'ok', 'counts': stats}, ensure_ascii=False))

if __name__ == '__main__':
    main()
