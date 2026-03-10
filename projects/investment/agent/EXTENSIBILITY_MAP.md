# Extensibility Map

## Purpose
This file explains which parts of the current investment system are:
- hard-coded in the codebase
- configurable by data files
- triggerable by OpenClaw through natural language
- not yet safely extensible

## 1. Already Natural-Language Friendly

These tasks already map well from natural language to existing workflows:

### Portfolio analysis
- questions like:
  - “我现在黄金是不是低配？”
  - “我的股票仓位偏离多少？”
- current route:
  - `portfolio_analyzer`
  - optionally `rebalancing_engine`

### Rebalance review
- questions like:
  - “现在需要再平衡吗？”
  - “哪些资产偏离太多？”
- current route:
  - `rebalancing_engine`

### Monthly plan
- questions like:
  - “这个月 12000 怎么投？”
- current route:
  - `monthly_planner`

### News and market review
- questions like:
  - “最近机器人和电网有什么新闻？”
  - “这些新闻会影响配置吗？”
- current route:
  - `news_collector`
  - optionally `portfolio_analyzer`
  - optionally `report_generator`

### Weekly / monthly reports
- questions like:
  - “给我一份本周周报”
  - “给我一份本月月报”
- current route:
  - `weekly-review`
  - `monthly-review`

## 2. Data-Driven But Not Yet Fully Natural-Language Editable

These parts are configurable, but until now they still relied on manual file edits
or Codex-side changes rather than a dedicated OpenClaw editing skill.

### Current portfolio objects
- source of truth:
  - `system/portfolio_state.json`
- extensibility status:
  - data-driven
  - now should be handled via `skills/portfolio_editor/skill.md`
  - production should be allowed to start from `system/portfolio_state.template.json`

### Previous portfolio snapshot
- source of truth:
  - `system/portfolio_state_previous.json`
- extensibility status:
  - data-driven
  - still needs disciplined update flow

### Asset research fixture
- source of truth:
  - `system/asset_research.json`
- extensibility status:
  - data-driven
  - now should be handled via `skills/research_editor/SKILL.md`
  - production should be allowed to start from `system/asset_research.template.json`

### Watchlists
- source of truth:
  - future `system/watchlists.json`
- extensibility status:
  - currently only a reserved interface with template
  - should become OpenClaw-editable later

## 3. Hard-Coded In Code Today

These parts are still primarily controlled by code and not safe to expand just by
natural-language edits alone.

### Supported asset query types
The code currently expects real-provider support only for a bounded set:
- `bond_fund`
- `etf`
- `index_fund`
- `thematic_fund`
- `commodity` for gold
- `cash` as explicit local model

Adding a new asset type usually requires code changes in:
- provider mapping
- signal logic
- report logic
- tests

### Provider mapping rules
- AKShare market/news adapters are hard-coded in provider factory logic
- symbol interpretation is still code-owned
- unsupported assets do not become queryable just because they appear in JSON

### Signal engine
- signal ids
- formulas
- thresholds
- evidence structure
are currently code-defined and test-defined

### Report schema
- weekly/monthly schema ids
- section ids
- summary fields
are now stabilized in code and documented in `storage/REPORT_SCHEMA.md`

## 4. Safely Extensible Next

These are the best candidates for future OpenClaw-driven extensibility.

### Portfolio object editing
- add/update/remove holdings
- validate required fields
- explain whether real providers support the asset
- support screenshot-driven `sync_snapshot`
- support resetting test portfolio into empty production state

### Research object editing
- add sector
- add companies
- add fair value
- add manager metadata
- add hot topics
- add recent bars when the user or a trusted source provides them

### Daily screenshot intake
- ingest total holdings screenshots
- ingest separate gold screenshots
- convert OCR results into structured portfolio objects
- validate before overriding the current snapshot

### Watchlist editing
- maintain weekly/monthly focus
- maintain custom topics for reports
- reserve hooks for future report personalization

### Watchlists and custom report focus
- “本周重点盯着机器人和黄金”
- “下次月报只突出低配和高估项”

These can be made data-driven without changing core formulas.

## 5. Not Yet Safe To Expose As Pure Natural-Language Editing

These should remain code-owned for now:
- new `asset_type` semantics
- new signal formulas
- provider implementation changes
- schema contract changes
- dynamic target-allocation regime switching

Reason:
- these changes affect correctness, not just content
- they require tests and coordinated updates across multiple layers

## Practical Rule
Use this distinction:

- OpenClaw natural-language extension is good for:
  - objects
  - content
  - watchlists
  - metadata
  - report focus

- Codex/code changes are still required for:
  - formulas
  - provider support
  - new asset-type semantics
  - schema contracts
  - risk-engine behavior
