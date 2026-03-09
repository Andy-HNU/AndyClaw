# 项目路线图

## 阶段 1：项目结构与数据基础设施
### 目标
把目录结构、SQLite 存储、数据源抽象、skill 接口和工作流固定下来。

实现职责：由 Codex 主导落地，OpenClaw 负责检查结构是否满足运行期调用和验收要求。

### 交付件
- `PROJECT.md` 中的结构说明
- `storage/SQLITE_SCHEMA.md`
- `src/investment_agent/db/schema.sql`
- `system/10_market_data_strategy.md`
- `agent/GITHUB_SKILL_DISCOVERY.md`
- `agent/PLAYBOOK_FULL_SYSTEM.md`

### 检测指标
- 目录分层清晰，源码目录已预留
- SQLite 表结构覆盖仓位、价格、新闻、信号、报告
- 数据源策略明确主源、备源、失败退化
- 关键规则只有一个权威版本

## 阶段 2：数据采集与存储
### 目标
实现市场数据/新闻数据写入 SQLite 的最小闭环。

实现职责：由 Codex 编写 provider、repository 与测试；OpenClaw 负责执行验收与失败反馈。

### 交付件
- `market_data_provider` 抽象接口
- `eastmoney_provider` 实现
- 可选 `akshare_provider` / `efinance_provider` 备源
- `repository` 层
- 测试通过：`../tests/TEST_SQLITE_STORAGE.md`、`../tests/TEST_MARKET_DATA_PROVIDER.md`

### 检测指标
- 能写入资产快照、价格快照、新闻快照
- 接口失败时可切换备源或返回可解释错误
- SQLite 查询结果能被后续服务复用

## 阶段 3：仓位分析与再平衡判断
### 目标
实现 `portfolio_analyzer` 与 `rebalancing_engine`。

实现职责：由 Codex 实现分析与判断逻辑；OpenClaw 负责调用、验收、记录问题。

### 交付件
- Python 模块：读取资产、计算总值、汇总占比、输出偏离
- Python 模块：按 ±10% 阈值判断是否进入再平衡检查
- 测试通过：`../tests/TEST_PORTFOLIO_RATIO.md`、`../tests/TEST_REBALANCE_TRIGGER.md`

### 检测指标
- 占比计算正确
- 输出结构稳定
- 能识别低配与高配
- 能给出优先使用新增资金的建议

## 阶段 4：定投规划与风险预警
### 目标
实现 `monthly_planner` 与 `risk_monitor`。

实现职责：由 Codex 实现；OpenClaw 负责在运行期对结果做测试映射与验收。

### 交付件
- Python 模块：根据低配情况分配月度资金
- 风险摘要输出
- 测试通过：`../tests/TEST_MONTHLY_INVESTMENT.md`

### 检测指标
- 定投建议不违背目标配置
- 风险提示能区分核心风险与观察项
- 当数据不完整时返回缺失字段而不是硬算

## 阶段 5：周报、月报与新闻收集
### 目标
实现 `report_generator` 与 `news_collector`，并跑通完整工作流。

实现职责：由 Codex 完成生成与整合能力；OpenClaw 负责工作流串联测试和报告验收。

### 交付件
- 周报模板
- 月报模板
- 新闻收集与归类能力
- 完整工作流实现
- 测试通过：`../tests/TEST_REPORTING_AND_NEWS.md`、`../tests/TEST_WORKFLOW_FULL.md`

### 检测指标
- 周报月报结构完整
- 新闻摘要区分事实、解读、待验证假设
- 建议部分不越权
- 工作流从数据刷新到报告输出可串联运行

## 阶段 6：OpenClaw 内化能力
### 目标
让 OpenClaw 不仅会调用代码，还知道何时调用、如何解释、失败时如何退化。

### 交付件
- 完整 skill 路由
- 示例对话
- 错误处理约定
- 阶段验收通过

### 检测指标
- 面对自然语言问题，能路由到正确 skill
- 数据不足时不会乱算
- 输出对用户和下一个 agent 都可继续使用
- Agent 能依据 playbook 自主串联多步工作流
