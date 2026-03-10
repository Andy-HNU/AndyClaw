# OpenClaw Control Surface

## Purpose
This file defines the stable interface surface that OpenClaw can use to operate
the investment system without changing core code.

## 1. Object-Level Control

OpenClaw should be able to manage these data objects through skills or structured
editing flows:

### Portfolio state
- file:
  - `system/portfolio_state.json`
- operations:
  - add holding
  - update holding
  - remove holding
  - sync full daily snapshot
  - reset to empty production state

### Previous portfolio snapshot
- file:
  - `system/portfolio_state_previous.json`
- operations:
  - rollover current snapshot before full sync
  - keep previous-day comparison base for signal engine

### Asset research
- file:
  - `system/asset_research.json`
- operations:
  - add asset research object
  - update sector / companies / fair value / manager / hot topics
  - mark missing research for newly added assets
  - start from `system/asset_research.template.json` in production if needed

### Watchlists and report focus
- recommended file:
  - `system/watchlists.template.json`
- operations:
  - add focus themes
  - remove focus themes
  - set report highlight rules

## 2. Workflow-Level Control

These are stable code entry points that OpenClaw should trigger, not rewrite:

- `init-db`
- `portfolio-summary`
- `rebalance-check`
- `persist-analysis`
- `refresh-prices`
- `persist-rebalance`
- `provider-capabilities`
- `monthly-plan`
- `signal-review`
- `weekly-review`
- `monthly-review`

OpenClaw should treat them as callable interfaces.

### Vision-first snapshot intake
- `import-snapshot --portfolio-image <path> --gold-image <path>`
- tries a vision model first
- falls back to local OCR automatically
- should be the default interface OpenClaw uses for screenshot parsing

### OCR intake
- `ocr-portfolio --portfolio-image <path> --gold-image <path>`
- returns structured candidate holdings for later sync

## 3. Daily Screenshot Intake Protocol

The user may provide one or more screenshots per day:
- total portfolio screenshot
- holdings screenshot with value / shares / profit / profit rate
- separate gold screenshot

OpenClaw should treat screenshot intake as:
- parse candidate fields
- build or update structured holdings
- validate completeness
- only then sync snapshot files

### Minimum fields per holding
- `name`
- `value`

### Strongly preferred fields
- `category`
- `asset_type`
- `symbol`
- `shares`
- `average_cost`
- `profit`

### Additional useful fields for future model evolution
- `profit_rate`
- `account`
- `captured_at`
- `notes`

## 4. Production Behavior

The current repository holdings can be treated as test data.

When the user starts real usage:
- production may start with an empty holdings file
- OpenClaw should know how to add the first asset from scratch
- OpenClaw should know how to delete assets that have been sold out
- OpenClaw should know how to replace the whole snapshot when daily screenshots
  are authoritative

Reference template:
- `system/portfolio_state.template.json`

## 5. Expansion Rule For New Assets

If a new asset is added, OpenClaw should assume it belongs in the full system and
check each layer explicitly:

### Data layer
- can it be stored in `portfolio_state.json`?

### Market data layer
- can the current provider fetch real quotes?

### Research layer
- does `asset_research.json` have a matching object?

### Signal layer
- can signal formulas operate on it with current fields?

### Report layer
- will weekly/monthly reports show it correctly?

### News layer
- is there a usable keyword or theme for news collection?

If any answer is "no":
- do not silently exclude the asset
- log the unsupported point
- convert it into a Codex implementation task if needed

## 6. Interfaces To Reserve Next

These are good candidates for future OpenClaw-controlled interfaces:

### Research editor
- maintain `asset_research.json`
- especially needed when new assets are added
 - should be the default path for natural-language research supplementation

### Snapshot importer
- dedicated ingestion interface for screenshot-derived payloads
- should separate vision/OCR extraction from portfolio validation
- should be the default Telegram screenshot entry point

### Watchlist editor
- maintain focus themes, sectors, or assets for reports and alerts
- should eventually write a runtime `watchlists.json` based on the template

### Task runner
- compose:
  - sync snapshot
  - refresh prices
  - signal review
  - weekly/monthly report

### Reminder scheduler
- trigger daily reminder to ask the user for fresh screenshots
- transport may be Telegram, but the investment system should only depend on
  receiving local image paths or attachment payloads
- future Telegram attachments should enter through `import-snapshot`
- see `TELEGRAM_DAILY_CAPTURE_FLOW.md`

## 7. Keep Code-Owned

These should remain Codex-owned for now:
- provider implementation
- new asset-type semantics
- signal formulas and thresholds
- report schema contracts
- dynamic allocation-regime logic
