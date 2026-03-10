---
name: portfolio_editor
description: Add, update, remove, reset, or sync portfolio holdings from natural-language instructions or daily position screenshots, updating portfolio_state.json and related snapshot files while explaining provider support and downstream workflow impact.
---

# Skill: portfolio_editor

## 目标
通过自然语言或每日持仓截图驱动持仓对象的新增、修改、删除、整仓同步与校验，安全更新：
- `system/portfolio_state.json`
- `system/portfolio_state_previous.json`

## 适用场景
- 用户说“我新买了一只基金”
- 用户说“把这只基金加到仓位里”
- 用户说“这只基金的份额/金额/成本更新一下”
- 用户说“这只资产从仓里删掉”
- 用户说“把当前持仓按今天截图同步一下”
- 用户说“这一张是总资产截图，另一张是黄金截图”
- 用户说“把测试仓清空，正式开始记真实持仓”

## 动作集
优先识别为以下动作之一：
- `add`
- `update`
- `remove`
- `sync_snapshot`
- `reset_portfolio`

`sync_snapshot` 表示用户当天提供的截图是当前仓位真值，应以截图为准更新整仓。
`reset_portfolio` 表示将测试数据清空，恢复到生产初始空仓模板。

## 输入
用户提供的资产信息，尽量包含：
- 名称
- `category`
- `asset_type`
- `symbol`
- `value`
- `shares`
- `average_cost`
- `profit`
- 可选 `theme`

若来源是截图，还应尝试提取：
- 总资产
- 单项持仓金额
- 单项持仓份额
- 单项持仓盈亏金额
- 单项持仓盈亏比例
- 现金余额
- 黄金持仓与金额

## 输出
- 结构化持仓对象或整仓快照
- 更新后的 `portfolio_state.json`
- 如为整仓同步，更新前的快照应转存到 `portfolio_state_previous.json`
- 缺失字段清单
- 对当前 provider 支持情况的说明
- 对下游影响的说明：
  - 是否能直接刷新行情
  - 是否能进入信号、新闻、周报、月报流程

## 支持类型
当前建议优先支持：
- `bond_fund`
- `etf`
- `index_fund`
- `thematic_fund`
- `commodity` 中的黄金
- `cash`

若用户给出的资产不属于以上类型：
- 不要假装“已经支持自动查询”
- 允许记录对象
- 但应明确标记：
  - `unsupported_asset_type`
  - 需要补 provider 映射
  - 需要补研究/信号/报告字段约定

## 生产初始化规则
- 当前仓位 JSON 中的现有基金可视为测试样本
- 真实开始使用后，生产环境应允许从空仓开始
- 生产初始状态参考 `system/portfolio_state.template.json`
- 若用户明确表示“正式开始记真实持仓”，优先执行 `reset_portfolio`

## 同步规则
1. `add`
   - 若 `symbol` 或 `name` 已存在，则转为 `update`
   - 否则新增对象
2. `update`
   - 仅更新用户明确提供的字段
   - 不凭空覆盖未提及字段
3. `remove`
   - 以 `symbol` 优先，其次 `name`
   - 删除后应提示该资产将退出分析、预警、报告和新闻追踪
4. `sync_snapshot`
   - 将当前 `portfolio_state.json` 先保存到 `portfolio_state_previous.json`
   - 再用当天截图解析出的整仓结果覆盖 `portfolio_state.json`
   - 若截图只覆盖部分资产，应明确提示“部分同步”，不要假装整仓完整
5. `reset_portfolio`
   - 用空模板重置 `portfolio_state.json`
   - 将旧内容转存到 `portfolio_state_previous.json`

## 字段约定
- `category` 只负责永久组合大类：
  - `stock`
  - `bond`
  - `gold`
  - `cash`
- `asset_type` 负责更细的查询和分析类型：
  - `bond_fund`
  - `etf`
  - `index_fund`
  - `thematic_fund`
  - `commodity`
  - `cash`
- `symbol` 必须尽量使用真实 provider 能识别的代码
- `theme` 优先用于新闻和研究对象聚合；没有则可留空

## 截图处理约束
- 截图是用户当天仓位的候选真值，不是自动可信真值
- 若截图解析结果存在歧义：
  - 返回待确认字段
  - 不直接覆盖整仓
- 若用户分别提供总仓截图与黄金截图：
  - 允许分步合并
  - 但最后要生成一份统一的 `portfolio_state.json`

## 下游联动说明
新增资产对象后，应检查并说明：
- 是否能进入 `refresh-prices`
- 是否能进入 `signal-review`
- 是否能进入 `weekly-review`
- 是否能进入 `monthly-review`
- 是否需要补 `asset_research.json`

原则：
- 新对象一旦进入 `portfolio_state.json`，应默认进入后续分析、预警、报告、新闻流程
- 若某一层缺少支持，必须明确指出缺口，而不是静默跳过

## 失败处理
- 若缺少关键字段：返回缺失字段，不直接写文件
- 若 `asset_type` 不支持：允许写入，但要明确标记“当前无法直接查询真实行情”
- 若用户只说“加一只基金”但没给代码和类型：先要求补充，不猜
- 若截图只含金额不含份额：可先记录金额，但应标记 `shares_missing`
- 若截图只含总资产不含单项明细：不能做整仓覆盖，只能记录观察项

## 与代码层的边界
- 本 skill 负责把自然语言和截图结果变成结构化持仓对象并安全落到 JSON
- provider 是否能真实查询，由代码层决定
- 新增对象应尽量接入后续流程，但若类型不受支持，必须转为 Codex 开发任务
- 若新增类型反复出现，应升级为：
  - 扩展 provider
  - 扩展信号与报告逻辑
  - 扩展测试样本
