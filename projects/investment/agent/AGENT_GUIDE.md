# Agent Guide

## 建议阅读顺序
1. `../system/00_context.md`
2. `../system/02_allocation_model.md`
3. `../system/05_rebalance_rule.md`
4. `SKILL_ROUTING.md`
5. `PROJECT_ROADMAP.md`
6. `../acceptance/PHASE_CHECKLIST.md`

## 处理任务的默认流程
1. 识别任务类型：仓位 / 风险 / 报告 / 新闻
2. 读取相关规则与数据
3. 按 `SKILL_ROUTING.md` 选择 skill
4. 若已有代码能力，则调用代码；若尚未实现，则按 skill 定义输出结构化开发任务，交由 Codex 实现
5. 对结果进行测试或验收映射
6. 形成结构化输出，并注明下一步

## 自然语言扩展边界
- 若用户是在补充或修改持仓对象，优先走 `portfolio_editor`
- 若用户给的是每日持仓截图，应先把截图信息转成结构化对象，再决定是局部更新还是整仓同步
- 若用户是在问分析、风险、报告，则优先走既有 workflow / skill
- 若用户是在引入新的资产类型、provider、信号规则、schema 结构，则应转为 Codex 开发任务，而不是仅靠 skill 文本扩展

## OpenClaw 控制面
- OpenClaw 负责对象层与工作流层操作，不负责核心算法改写
- 对象层包括：
  - 当前持仓
  - 上期快照
  - 后续可扩展到研究对象与 watchlist
- 工作流层包括：
  - 行情刷新
  - 信号复核
  - 周报月报
- 统一参考：
  - `OPENCLAW_CONTROL_SURFACE.md`

## 文档与代码的衔接原则
- 文档先定义规则
- skill 定义接口
- 路线图安排 Codex 的实现顺序与 OpenClaw 的验收顺序
- 测试规格定义正确性
- 阶段验收定义是否通过
