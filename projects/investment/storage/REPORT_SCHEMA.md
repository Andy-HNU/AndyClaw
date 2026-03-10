# Report Schema

## Purpose
This document fixes the stable JSON/Markdown report structure that OpenClaw and
future tooling should expect from the current investment project.

## JSON Root Fields

All stored reports should include:
- `schema_version`
- `report_type`
- `report_time`
- `title`
- `summary`
- `sections`

## Common Section Keys

Each section should include:
- `section_id`
- `title`
- `items`

Each item may include:
- `label`
- `value`
- `details`

## Weekly Report

### Required sections
- `portfolio_snapshot`
- `position_changes`
- `risk_summary`
- `news_summary`
- `watchlist`

### Weekly summary expectations
- latest total portfolio value
- category allocations
- top position changes
- open risk signals
- important news headlines
- next actions / watch items

## Monthly Report

### Required sections
- `portfolio_snapshot`
- `position_changes`
- `rebalance_review`
- `monthly_plan`
- `risk_summary`
- `research_highlights`
- `news_summary`
- `watchlist`

### Monthly summary expectations
- month-end total portfolio value
- category allocations and deviations
- rebalance trigger result
- monthly capital allocation plan
- risk signals
- asset research highlights
- major news observations
- next-month watchlist

## Stability Rules
- new sections may be added, but existing required section ids should not be renamed casually
- report consumers should read by `section_id`, not by markdown heading text
- risk items should preserve signal ids and evidence when available
- position items should preserve amount/share change fields when available
