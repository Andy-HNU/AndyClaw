---
name: self-improvement-lite
description: 轻量自我改进记录技能。用于把错误、用户纠正、知识缺口、功能诉求写入 `.learnings/`，并在每天回顾时将高价值经验提升到 AGENTS.md / SOUL.md / TOOLS.md / MEMORY.md。适用于“避免重复犯错、沉淀经验、降低长期 token 浪费”的场景；默认不启用高频 hooks。
---

# Self-Improvement Lite

只做高价值、低开销闭环：记录 → 回顾 → 提升。

## 1) 文件结构

在工作区维护：

- `.learnings/LEARNINGS.md`：纠正、最佳实践、知识缺口
- `.learnings/ERRORS.md`：命令失败、异常、外部集成故障
- `.learnings/FEATURE_REQUESTS.md`：用户提出的新能力

若目录不存在，先创建。

## 2) 记录触发条件

出现以下情况立刻记录：

- 用户纠正我
- 命令/脚本执行失败
- 发现知识已过时
- 用户提出新能力需求
- 发现更优流程/更稳妥做法

## 3) 记录格式（精简）

每条记录包含：

- ID（LRN/ERR/FEAT-YYYYMMDD-XXX）
- 时间（ISO-8601）
- 优先级（low/medium/high/critical）
- 状态（pending/resolved/promoted）
- 一句话摘要
- 关键上下文
- 下一步动作
- 关联文件

详细模板见：`references/templates.md`

## 4) 每日回顾与提升

在每日回顾（00:00 任务）中执行：

1. 合并同类问题（避免重复记录）
2. 对重复出现 ≥2 次的问题提升优先级
3. 将“跨任务通用规则”提升到：
   - 行为风格 → `SOUL.md`
   - 工作流程 → `AGENTS.md`
   - 工具坑位 → `TOOLS.md`
   - 长期事实/约定 → `MEMORY.md`
4. 将已落地的记录标为 `promoted` 或 `resolved`

## 5) Token 使用规则

- 默认禁用每轮提示的高频 hook
- 优先在“事件发生时手动记录 + 00:00 批量回顾”
- 避免把低价值噪音写入学习日志

## 6) 边界

- 不记录明文密钥/密码/token
- 敏感内容仅记录引用位置，不记录原文
- 外部仓库引入结论写到 ERRORS/LEARNINGS 时，附扫描结论摘要
