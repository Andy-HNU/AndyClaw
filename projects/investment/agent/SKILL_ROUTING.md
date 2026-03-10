# Skill Routing

## 路由原则
用户问题先归类，再调用已实现 skill；若涉及数据库或行情刷新，先走数据层，再走分析层，再走报告层。

若某项能力尚未实现，不假装“可以直接调用”，而是输出结构化开发任务并交给 Codex。

## 任务 -> skill / 服务 映射
### 1. 仓位管理
触发词：仓位、占比、配置、低配、高配、偏离
调用：
- `portfolio_analyzer`
- `rebalancing_engine`
- 必要时先刷新 `market_data_provider`

### 2. 风险预警
触发词：风险、预警、集中、偏离、回撤、防守
调用：
- `portfolio_analyzer`
- `rebalancing_engine`
- `risk_monitor`
- `report_generator`（用于输出风险摘要）

### 3. 周报月报
触发词：周报、月报、复盘、汇总、报告
调用：
- `portfolio_analyzer`
- `rebalancing_engine`
- `report_generator`
- 若需要最新数据，先调用 `market_data_provider`

### 4. 新闻信息收集与投资建议
触发词：新闻、政策、宏观、行业动态、今天发生了什么、怎么看
调用：
- `news_collector`
- 必要时调用 `market_data_provider` 获取板块/指数背景
- 再调用 `portfolio_analyzer` 判断对仓位的影响
- 最终由 `report_generator` 输出观察项或建议摘要

### 5. 数据刷新与入库
触发词：更新数据、刷新行情、同步新闻、写入数据库
调用：
- `market_data_provider`
- `repository`
- 成功后才能进入分析与报告环节

### 6. 持仓对象维护
触发词：新增基金、加一只基金、删掉这只基金、更新份额、更新成本、修改持仓对象、按截图同步持仓、清空测试仓
调用：
- `portfolio_editor`
- 成功后再进入：
  - `market_data_provider`
  - `portfolio_analyzer`
  - `weekly-review` / `monthly-review`

### 7. 截图导入
触发词：今日持仓截图、OCR、识别截图、Telegram发来的持仓图、同步今日仓位截图
调用：
- `snapshot_importer`
- 成功后再进入：
  - `portfolio_editor`
  - `market_data_provider`
  - `signal-review`
  - `weekly-review` / `monthly-review`
说明：
- 默认走 `import-snapshot`
- 只有视觉链路不可用或失败时才回退到 `ocr-portfolio`

### 8. 研究对象维护
触发词：补研究、补板块、补公司、更新基金经理、补估值、补夏普比、研究对象
调用：
- `research_editor`
- 必要时再进入：
  - `signal-review`
  - `weekly-review` / `monthly-review`

### 9. 外部能力补充
触发词：现成项目、开源实现、GitHub、参考仓库、搜索现有 skill
调用：
- 先阅读 `agent/GITHUB_SKILL_DISCOVERY.md`
- 按查询模板在 GitHub 检索
- 默认作为 Codex 的实现参考输入
- 仅吸收结构、接口、测试思路，不直接照搬未经审查代码

## 未实现能力处理规则
- 如果 `portfolio_analyzer`、`repository`、`market_data_provider` 等能力尚未落地，OpenClaw 应明确说明“能力未实现”。
- 输出内容应转为：
  - 目标
  - 输入输出
  - 依赖数据
  - 测试规格映射
  - 建议交付给 Codex 的实现任务
- 不把尚未存在的代码路径伪装成可执行步骤。

## 兜底规则
- 若问题缺少资产数据，先标记数据不足
- 若问题缺少时间范围，报告类默认按最近一周或最近一月模板输出
- 若新闻证据不足，只输出观察项，不输出买卖建议
- 若主数据源失败，先切换备源；若备源也失败，输出“数据刷新失败”并保留上次快照
- 若用户新增的是当前未支持的资产类型，应明确说明“对象可记录，但暂不能直接查询真实行情”
- 若用户提供的是整仓截图，应优先走 `sync_snapshot`，并在覆盖前保留上一版快照
- 若用户先给的是截图原图，应先走 `snapshot_importer`，不要直接手改持仓对象
- 若用户新增资产后缺少研究对象，应明确提示转入 `research_editor`
