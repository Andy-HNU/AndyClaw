---
name: snapshot_importer
description: Import daily portfolio screenshots from local files or future Telegram attachments, use a vision model first and OCR as fallback, then hand structured candidate objects to portfolio_editor for validated sync.
---

# Skill: snapshot_importer

## 目标
把用户发送的持仓截图转成结构化候选快照，供 `portfolio_editor` 做最终校验和写入。

## 适用场景
- 用户说“这是我今天的持仓截图”
- 用户说“这是总仓图，黄金我单独发一张”
- 用户通过 Telegram 发来两张图片，要求同步今日仓位

## 输入
- 持仓总览截图
- 可选黄金截图
- 可选用户补充说明

## 输出
- 视觉模型或 OCR 的原始候选结果
- 结构化候选持仓对象
- 缺失字段清单
- 建议后续动作：
  - `portfolio_editor`
  - `refresh-prices`
  - `signal-review`
  - `weekly-review` / `monthly-review`

## 工作流
1. 优先调用 `import-snapshot`
2. 若视觉模型不可用或失败，自动回退到 `ocr-portfolio`
3. 检查缺失字段
4. 若字段可接受，则交给 `portfolio_editor` 执行 `sync_snapshot`
5. 同步后再触发价格刷新与报告工作流

## 使用约束
- 视觉模型结果只是候选值，不是自动真值
- OCR 结果只是候选值，不是自动真值
- 若金额、份额、代码识别不清，应要求用户确认
- 若总览图不含黄金，而用户又单独发黄金图，应合并两者后再同步

## Telegram 预留流程
- 定时提醒用户上传今日持仓截图
- 接收 Telegram 图片后写到本地临时路径
- 把本地图片路径优先交给 `import-snapshot`
- 若视觉链路失败，再走 `ocr-portfolio`
- 再交给 `portfolio_editor`

## 与代码层边界
- 本 skill 不负责 OCR 模型实现
- 本 skill 不直接改核心分析逻辑
- 本 skill 只负责编排截图导入和后续工作流衔接
