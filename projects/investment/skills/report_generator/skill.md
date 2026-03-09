# Skill: report_generator

## 目标
输出周报或月报。

## 对应项目目的
- 风险预警
- 周报月报
- 投资辅助建议

## 输入
- `portfolio_analyzer` 结果
- `rebalancing_engine` 结果
- `monthly_planner` 结果（用于月报）
- `news_collector` 结果（用于周报或月报）

## 输出
- 周报或月报 markdown
- 结论摘要
- 风险摘要
- 观察项

## 步骤
1. 识别报告类型
2. 汇总仓位、风险、建议、新闻
3. 用固定模板生成报告

## 失败处理
- 缺少新闻时，可只输出仓位与风险部分
- 缺少月度建议时，月报中明确标记待补充
