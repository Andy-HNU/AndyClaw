# 月度复盘工作流

1. 执行 `PLAYBOOK_DAILY_REFRESH.md` 刷新月末数据
2. 读取 `../system/portfolio_state.json` 与 SQLite 最新快照
3. 调用 `portfolio_analyzer`
4. 调用 `rebalancing_engine`
5. 调用 `monthly_planner`
6. 调用 `risk_monitor`
7. 调用 `report_generator`
8. 输出：
   - 当前资产比例
   - 是否触发再平衡检查
   - 本月定投建议
   - 核心风险与下月观察点
