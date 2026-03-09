CREATE TABLE IF NOT EXISTS portfolio_assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_code TEXT NOT NULL,
    asset_name TEXT NOT NULL,
    category TEXT NOT NULL,
    subcategory TEXT,
    quantity REAL,
    market_value REAL NOT NULL,
    cost_basis REAL,
    currency TEXT DEFAULT 'CNY',
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS portfolio_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_time TEXT NOT NULL,
    total_value REAL NOT NULL,
    stock_value REAL,
    bond_value REAL,
    gold_value REAL,
    cash_value REAL,
    note TEXT
);

CREATE TABLE IF NOT EXISTS price_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_code TEXT NOT NULL,
    source TEXT NOT NULL,
    trade_date TEXT NOT NULL,
    close_price REAL,
    high_price REAL,
    low_price REAL,
    volume REAL,
    fetched_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS news_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT,
    url TEXT,
    published_at TEXT,
    topic TEXT,
    sentiment_hint TEXT,
    fetched_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS analysis_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_time TEXT NOT NULL,
    total_value REAL NOT NULL,
    allocation_json TEXT NOT NULL,
    deviation_json TEXT NOT NULL,
    status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS risk_signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    signal_time TEXT NOT NULL,
    signal_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    message TEXT NOT NULL,
    evidence_json TEXT,
    status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS investment_suggestions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    suggestion_time TEXT NOT NULL,
    suggestion_type TEXT NOT NULL,
    content_json TEXT NOT NULL,
    rationale TEXT,
    status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_time TEXT NOT NULL,
    report_type TEXT NOT NULL,
    title TEXT NOT NULL,
    content_md TEXT,
    content_json TEXT
);
