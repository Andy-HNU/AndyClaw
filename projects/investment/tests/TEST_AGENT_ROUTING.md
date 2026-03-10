# 测试：Agent 路由

## 用例 1
用户说：我现在黄金是不是低配？

### 预期
- 调用 `portfolio_analyzer`
- 必要时调用 `rebalancing_engine`

## 用例 2
用户说：给我一份本月投资月报。

### 预期
- 调用 `portfolio_analyzer`
- 调用 `rebalancing_engine`
- 调用 `monthly_planner`
- 调用 `report_generator`

## 用例 3
用户说：最近机器人和电网有什么重要新闻，会影响我的配置吗？

### 预期
- 调用 `news_collector`
- 必要时调用 `portfolio_analyzer`
- 最终输出观察项或建议摘要

## 用例 4
用户说：给我一份本周投资周报。

### 预期
- 调用 `weekly_review_workflow`
- 输出本周仓位变化、风险、新闻和待验证事项

## 用例 5
用户说：我仓里新买了一只债基，代码是 123456，帮我加进去。

### 预期
- 调用 `portfolio_editor`
- 若字段完整，则更新持仓对象
- 若类型支持，则说明后续可直接刷新行情和进入报告工作流
- 若类型不支持，则明确提示需要补 provider 支持

## 用例 6
用户说：这是我今天的持仓截图，帮我把仓位同步进去，黄金我单独再发一张图。

### 预期
- 调用 `portfolio_editor`
- 先识别为 `sync_snapshot`
- 若截图信息不完整，则返回待确认字段
- 若截图信息完整，则先保留上一版快照，再更新当前持仓
- 更新后说明哪些资产已经进入行情、信号、报告流程，哪些还缺 provider / research 支持

## 用例 7
用户说：新加的机器人基金，帮我补一下板块、基金经理、热点和估值。

### 预期
- 调用 `research_editor`
- 以资产 code 或主题定位研究对象
- 更新 `asset_research.json`
- 说明更新后该资产可进入研究摘要与估值类信号

## 用例 8
用户说：我通过 Telegram 发了两张图给你，一张总持仓，一张黄金，帮我同步今天仓位。

### 预期
- 先调用 `snapshot_importer`
- 默认经由 `import-snapshot`
- 再调用 `portfolio_editor`
- 若 OCR 缺字段，则返回待确认项
- 若 OCR 结果可接受，则同步快照并继续走刷新价格与报告流程

## 用例 9
用户说：帮我跑一下今天的日报，看看要不要调仓，顺便看看今天机器人和黄金的新闻。

### 预期
- 调用 `daily-review`
- 输出当日仓位检查、风险摘要、新闻摘要和建议动作

## 用例 10
用户说：每月 15 号工资日提醒我给出仓位和收入金额，并给出平衡仓位建议。

### 预期
- 不要求立即新增硬编码 workflow
- 先把它理解成一个自然语言周期任务定义
- 后续由 OpenClaw runtime / scheduler 层消费

## 用例 11
用户说：每日 14:30 检查我仓里所有基金，获取实时盘情并给出预警。

### 预期
- 先解析为 recurring task intent
- 底层预期调用：
  - `refresh-prices`
  - `signal-review`
  - 必要时 `daily-review`

## 用例 12
用户说：帮我调查一下机器人 ETF，给我按平时习惯整理新闻和观察点。

### 预期
- 调用新闻/研究相关能力
- 输出结构化新闻摘要和观察项
- 不应要求先新增固定代码 workflow
