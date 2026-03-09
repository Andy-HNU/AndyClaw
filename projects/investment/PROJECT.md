# investment / PROJECT

## 项目定位
这是 OpenClaw workspace 中的投资项目 overlay，也是后续 Python 项目的产品、开发与交接入口。

目标不是直接替用户下单，而是构建一个由 Codex 主导开发实现、由 OpenClaw 主导运行调用与测试验收的投资辅助系统，用于：
- 管理仓位
- 风险预警
- 生成周报与月报
- 收集新闻信息并形成投资辅助建议

## 项目目的
1. 管理仓位
2. 风险预警
3. 周报月报
4. 新闻信息收集和投资建议

## 设计原则
- 长期框架优先，不做短线交易驱动
- 先文档化，再工具化，再自动化
- 自动化默认用于记录、计算、预警、汇总，不直接替代用户做资金决策
- 所有能力都要有输入、输出、测试与验收标准
- 项目必须方便下一位 agent / Codex 接手
- 数据源、存储层、分析层、工作流层必须解耦

## 推荐项目结构
本项目建议在 `projects/investment/` 下继续落成一个可运行的 Python 项目，推荐结构如下：

```text
investment/
├─ PROJECT.md
├─ PROFILE.md
├─ RULES.md
├─ system/                      # 投资规则、资产状态、目标配置、数据源策略
├─ agent/                       # agent 身份、路线图、路由、工作流、GitHub 检索指导
├─ skills/                      # skill 定义，负责让 agent 知道何时调用什么能力
├─ tests/                       # 测试规格（单元 / 集成 / 工作流）
├─ acceptance/                  # 阶段验收
├─ storage/                     # SQLite 相关文档与 schema
├─ src/
│  └─ investment_agent/
│     ├─ config.py
│     ├─ main.py
│     ├─ models/                # 数据模型
│     ├─ db/                    # SQLite 连接、schema、repository
│     ├─ providers/             # 行情/新闻数据源抽象与实现
│     ├─ services/              # portfolio_analyzer 等核心服务
│     ├─ workflows/             # 日报/周报/月报/再平衡工作流
│     ├─ reports/               # 报表模板与渲染
│     └─ utils/                 # 通用工具
└─ examples/                    # 样例输入输出与对话
```

## 技术基线
### 存储
- 使用 SQLite 作为默认本地数据库
- 目标：低部署成本、易备份、便于 Agent 与 Codex 在 workspace 内直接维护
- 数据库存放建议：`data/investment.db`

### 数据接口
优先顺序建议如下：
1. 若用户拥有东方财富 Choice 量化接口权限，则优先对接官方接口
2. 若没有官方权限，则优先尝试社区封装的东方财富相关数据源适配层
3. 至少保留一个备用源，避免单一接口失效导致系统停摆

### 能力实现方式
- 代码核心放在 `src/investment_agent/`
- Codex 负责实现数据库、provider、services、workflows、reports 与测试代码
- OpenClaw 通过 `skills/*/skill.md` 理解能力边界与调用方式
- OpenClaw 通过 `agent/PLAYBOOK_*.md` 执行测试、验收和运行期串联
- 测试规格与阶段验收驱动 Codex 迭代开发

## 关键模块
### 1. 仓位与配置
- portfolio_analyzer
- rebalancing_engine
- monthly_planner

### 2. 风险与预警
- risk_monitor
- rebalancing_engine
- report_generator

### 3. 报告系统
- report_generator
- weekly_review_workflow
- monthly_review_workflow

### 4. 信息收集
- news_collector
- market_data_provider
- 可选 GitHub 检索辅助能力

## 当前范围
- 资产配置模型
- 每月定投规则
- 再平衡规则
- 风险控制规则
- 新闻收集与辅助建议边界
- skills 驱动的开发路线
- 阶段目标、测试用例、交付件检视
- SQLite 数据模型与数据源策略
- 完整工作流定义

## 当前状态
- 已完成：workspace 骨架、投资项目 overlay、投资系统主规则、skills/工作流/测试/验收框架
- 本次新增：项目结构建议、SQLite 方案、数据源策略、GitHub 检索指导、完整工作流
- 第一阶段已完成：可运行的 SQLite 初始化、首份资产快照入库、当前仓位占比分析 CLI、再平衡触发检查 CLI、`unittest` 基线验证
- 第二阶段基线已完成：`market_data_provider` 抽象、本地主/备源退化、价格快照入库、分析结果持久化
- 未完成：真实行情/新闻数据抓取、自动报表、工作流调度、OpenClaw 运行期验收闭环

## 目录地图
- `system/`：投资系统文档、资产数据、目标配置、数据源策略
- `agent/`：agent 身份、路线图、路由、完整工作流、GitHub 检索指导
- `skills/`：按能力拆分的 skill 定义
- `tests/`：测试规格
- `acceptance/`：阶段验收清单
- `storage/`：SQLite 表结构、字段约定、迁移要求
- `src/`：由 Codex 主导实现的 Python 项目源码目录
- `examples/`：样例输入输出

## 开发顺序建议
1. 先落 SQLite schema 与 repository 层
2. 再做 market data provider 抽象与东方财富实现
3. 然后实现 portfolio_analyzer 与 rebalancing_engine
4. 再实现 monthly_planner 与 risk_monitor
5. 最后实现周报月报、新闻收集、完整工作流
6. 完成后再由 OpenClaw 接入日常调用、测试与验收

## 统一入口
先读：
- `agent/AGENT_IDENTITY.md`
- `system/00_context.md`
- `agent/AGENT_GUIDE.md`
- `agent/SKILL_ROUTING.md`
- `agent/PROJECT_ROADMAP.md`
- `agent/PLAYBOOK_FULL_SYSTEM.md`
- `acceptance/PHASE_CHECKLIST.md`

## 下一步
1. 在当前抽象后接入真实 `market_data_provider` 实现
2. 将再平衡结果写入 `investment_suggestions` 或 `risk_signals`
3. 新增新闻抓取与入库基线
4. 将当前 `unittest` 基线扩展到真实 provider 适配与失败退化测试
5. 准备 OpenClaw 调用用的验收 playbook 与阶段回测
