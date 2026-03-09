# openclaw / PROJECT

## 项目目标
构建适合用户自身工作方式的 OpenClaw 体系，使 agent 能长期接手项目，而不是依赖单轮 prompt。

## 当前原则
- 以 markdown 规则和项目文档驱动行为
- 以 skills / 项目模块拆分复杂任务
- 让 Codex 能根据文档直接实现
- 避免过度集中式 main 进程设计
- 优先支持 agent 接手，而不是单次脚本运行

## 当前关注点
- AGENTS / USER / SOUL / MEMORY 的边界
- root 层与 project overlay 的关系
- skills 列表与触发方式
- 项目阶段目标
- 验收标准与测试用例
- 如何把 Python 项目内化为 agent 能力

## 当前状态
- 已完成：基础治理思路、Codex 与 OpenClaw 分工思路、workspace 骨架方案
- 进行中：部署包准备与部署流程设计
- 未完成：真实运行反馈下的规则收敛、skills 路线图细化

## 风险点
- 让 agent 在未设边界下自由改写自己
- root 层文件被过多项目差异污染
- 只做文档不做闭环运行

## 下一步
- 由 Codex 完成工作区骨架部署
- 由 OpenClaw 在骨架内运行并沉淀
- 根据实际使用情况增加项目与规则
