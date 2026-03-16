#!/usr/bin/env python3
import argparse
import sqlite3
from pathlib import Path

SCHEMA = '''
CREATE TABLE IF NOT EXISTS domain_knowledge (
  id INTEGER PRIMARY KEY,
  domain TEXT NOT NULL,
  topic TEXT NOT NULL,
  content TEXT NOT NULL,
  key_numbers TEXT,
  updated_at DATE DEFAULT (date('now')),
  UNIQUE(domain, topic)
);

CREATE TABLE IF NOT EXISTS historical_reference (
  id INTEGER PRIMARY KEY,
  event_type TEXT NOT NULL,
  year INTEGER NOT NULL,
  description TEXT NOT NULL,
  outcome TEXT,
  analogy_power INTEGER CHECK(analogy_power BETWEEN 1 AND 5),
  UNIQUE(event_type, year, description)
);

CREATE TABLE IF NOT EXISTS current_state (
  id INTEGER PRIMARY KEY,
  category TEXT NOT NULL,
  key TEXT NOT NULL,
  value TEXT NOT NULL,
  context TEXT,
  valid_until DATE,
  UNIQUE(category, key)
);
'''

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--db', default='memory/policy_knowledge.db')
    args = p.parse_args()

    db = Path(args.db)
    db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
    print(f'initialized: {db}')

if __name__ == '__main__':
    main()
