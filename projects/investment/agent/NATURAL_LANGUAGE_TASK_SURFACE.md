# Natural Language Task Surface

## Purpose
This file describes the kinds of natural-language tasks OpenClaw should be able
to understand and orchestrate on top of the investment system.

## Design Rule
- The codebase provides stable primitives and workflows.
- OpenClaw is responsible for interpreting user language and composing those primitives.
- Not every recurring task should be hard-coded as a dedicated workflow.

## 1. Direct Trigger Tasks

Examples:
- “帮我调查 xxx ETF”
- “看看今天机器人和黄金有什么新闻”
- “现在要不要再平衡”
- “帮我跑一下今天的日报”

Expected OpenClaw behavior:
- map the request to existing skills and workflows
- gather data
- return a structured answer or report

## 2. Recurring Task Intents

Examples:
- “每月 15 号工资日提醒我给出仓位和收入金额，并给出平衡仓位建议”
- “每日 9 点给我机器人板块热点”
- “每日 14:30 检查我仓里的基金，给出预警和建议”

Expected OpenClaw behavior:
- parse the recurrence, trigger time, and task intent
- convert them into a structured runtime task definition
- later hand them to a scheduler/runtime layer

Important:
- the investment project should not hard-code every possible schedule pattern
- OpenClaw should keep room for new natural-language recurring intents

## 3. Recommended Task Definition Shape

Suggested runtime structure:
- `task_name`
- `task_type`
- `trigger_type`
- `schedule`
- `input_scope`
- `workflow_steps`
- `output_expectation`
- `notes`

## 4. Stable Task Types To Support First

- `daily_portfolio_review`
- `daily_sector_news`
- `weekly_summary`
- `monthly_summary`
- `salary_day_rebalance_prompt`
- `intraday_market_watch`
- `asset_investigation`

## 5. Current Primitive Building Blocks

OpenClaw should compose these instead of inventing ad-hoc code paths:
- `import-snapshot`
- `portfolio_editor`
- `refresh-prices`
- `rebalance-check`
- `signal-review`
- `daily-review`
- `weekly-review`
- `monthly-review`
- `research_editor`

## 6. Runtime Gap Kept Open Intentionally

The following layer is intentionally not hard-coded yet:
- scheduler persistence
- reminder delivery
- trigger execution daemon
- arbitrary recurring task registry

These should stay flexible because user phrasing and timing needs will change.
