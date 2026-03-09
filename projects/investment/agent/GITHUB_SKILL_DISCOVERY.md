# GitHub 检索现有能力指导

## 目标
当项目某一层能力缺实现时，允许 OpenClaw / Codex 去 GitHub 检索可参考的现有项目，但只能吸收结构、接口、测试与失败处理思路。

## 优先检索对象
1. SQLite 仓位管理项目
2. A 股 / ETF / 基金数据获取项目
3. 周报月报生成项目
4. 新闻抓取与摘要项目
5. 带测试与清晰目录结构的 Python 项目

## 推荐查询模板
- `python sqlite portfolio tracker akshare`
- `python efinance etf portfolio sqlite`
- `stock report generator python sqlite`
- `financial news collector python eastmoney`
- `python investment workflow tests`

## 选择标准
- 最近仍有维护
- 有明确许可证
- 有测试目录
- 有 requirements / pyproject
- 有模块化结构
- 对数据源失败有处理策略

## 吸收方式
只吸收：
- 目录结构
- 抽象接口
- provider/repository 分层
- schema 设计
- 测试样式
- 错误处理模式

不要直接照搬：
- 未审查的大段业务代码
- 不明许可证代码
- 带硬编码密钥的实现
- 与本项目长期配置哲学冲突的交易逻辑

## 记录要求
每次参考 GitHub 代码后，必须记录：
- 仓库地址
- 参考了什么
- 为什么采用
- 改了什么
- 为什么不直接复制
