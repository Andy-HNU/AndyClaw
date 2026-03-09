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

## 文档与代码的衔接原则
- 文档先定义规则
- skill 定义接口
- 路线图安排 Codex 的实现顺序与 OpenClaw 的验收顺序
- 测试规格定义正确性
- 阶段验收定义是否通过
