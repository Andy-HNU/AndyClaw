---
name: research_editor
description: Add, update, remove, or audit asset research objects in asset_research.json so newly added holdings can participate in signal evaluation, report highlights, news topic mapping, and future watchlist workflows.
---

# Skill: research_editor

## 目标
通过自然语言维护 `system/asset_research.json`，让新增或变更后的资产具备研究层数据，能够进入：
- `signal-review`
- `weekly-review`
- `monthly-review`
- 新闻主题聚合

## 适用场景
- 用户说“给这只基金补一下板块和公司信息”
- 用户说“这只资产需要加估值和夏普比”
- 用户说“把这个基金经理更新掉”
- 用户说“新加的资产研究信息补全一下”
- 用户说“这个研究对象删掉”

## 动作集
- `add`
- `update`
- `remove`
- `audit_missing_research`

`audit_missing_research` 用于检查当前持仓中哪些资产还没有研究对象。

## 输入
研究对象尽量包含：
- `asset_code`
- `sector`
- `companies`
- `fund_manager`
- `hot_topics`
- `current_price`
- `fair_value`
- `sharpe_ratio`
- `category_sharpe`
- `max_drawdown`
- `category_max_drawdown`
- `volatility`
- `category_volatility`
- `recent_bars`

## 输出
- 结构化研究对象
- 更新后的 `asset_research.json`
- 缺失字段清单
- 对当前信号和报告影响的说明

## 关键约定
- `asset_code` 应与持仓中的 `theme` 优先对齐；若没有 `theme`，则与 `name` 对齐
- `companies` 与 `hot_topics` 应始终为列表
- `recent_bars` 仅在用户明确提供或已有样本时维护；不凭空伪造历史序列

## 最低可用字段
若只是为了让新资产进入研究与报告层，至少应补：
- `asset_code`
- `sector`
- `hot_topics`

若要支持完整信号评估，至少还应补：
- `current_price`
- `fair_value`
- `recent_bars`

## 同步规则
1. `add`
   - 若 `asset_code` 已存在，则转为 `update`
2. `update`
   - 只更新用户明确给出的字段
   - 不清空未提及字段
3. `remove`
   - 删除后必须提示：该资产仍可存在于持仓，但研究摘要和部分信号会退化
4. `audit_missing_research`
   - 对照 `portfolio_state.json`
   - 输出缺少研究对象的资产清单
   - 优先提示需要最少补哪些字段

## 下游联动说明
研究对象更新后，应说明：
- 是否足以进入 `research_highlights`
- 是否足以支持估值类信号
- 是否足以支持趋势/量价类信号
- 是否足以改善新闻主题聚合

## 失败处理
- 若缺少 `asset_code`：不写文件
- 若用户只说“补研究”但没说明是哪只资产：先要求定位资产
- 若用户给的是结论型话术、没有证据字段，应记录为观察项，不要伪装成量化字段

## 与代码层的边界
- 本 skill 只维护研究对象数据
- 不改信号公式
- 不改 provider
- 不改报告 schema
- 若研究字段结构需要大改，应转为 Codex 开发任务
