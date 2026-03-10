# 测试：Agent 路由

## 用例 1
用户说：我现在黄金是不是低配？

### 预期
- 调用 `portfolio_analyzer`
- 必要时调用 `rebalancing_engine`

## 用例 2
用户说：给我一份本月投资月报。

### 预期
- 调用 `portfolio_analyzer`
- 调用 `rebalancing_engine`
- 调用 `monthly_planner`
- 调用 `report_generator`

## 用例 3
用户说：最近机器人和电网有什么重要新闻，会影响我的配置吗？

### 预期
- 调用 `news_collector`
- 必要时调用 `portfolio_analyzer`
- 最终输出观察项或建议摘要

## 用例 4
用户说：给我一份本周投资周报。

### 预期
- 调用 `weekly_review_workflow`
- 输出本周仓位变化、风险、新闻和待验证事项
