# SQLite 存储设计

## 目标
使用 SQLite 作为本地单文件数据库，支持：
- 资产状态快照
- 价格快照
- 新闻快照
- 分析结果
- 风险信号
- 周报月报

## 数据库文件
建议路径：`data/investment.db`

## 核心表
### 1. portfolio_assets
保存当前资产条目。
字段：
- id
- asset_code
- asset_name
- category
- subcategory
- quantity
- market_value
- cost_basis
- currency
- updated_at

### 2. portfolio_snapshots
保存按时间聚合后的仓位快照。
字段：
- id
- snapshot_time
- total_value
- stock_value
- bond_value
- gold_value
- cash_value
- note

### 3. price_snapshots
保存标的价格快照。
字段：
- id
- asset_code
- source
- trade_date
- close_price
- high_price
- low_price
- volume
- fetched_at

### 4. news_items
保存新闻原文与元数据。
字段：
- id
- source
- title
- summary
- url
- published_at
- topic
- sentiment_hint
- fetched_at

### 5. analysis_results
保存仓位分析与偏离结果。
字段：
- id
- analysis_time
- total_value
- allocation_json
- deviation_json
- status

### 6. risk_signals
保存风险预警。
字段：
- id
- signal_time
- signal_type
- severity
- message
- evidence_json

### 7. investment_suggestions
保存每月定投或再平衡建议。
字段：
- id
- suggestion_time
- suggestion_type
- content_json
- rationale
- status

### 8. reports
保存周报与月报。
字段：
- id
- report_time
- report_type
- title
- content_md
- content_json

## 约束要求
- 所有时间字段统一使用 ISO 8601
- JSON 字段必须保持结构稳定
- 所有表保留 `source` 或 `status` 字段，方便追查
- 写入失败必须可重试，不允许静默吞错
