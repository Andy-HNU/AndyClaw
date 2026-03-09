# 周报工作流

1. 执行 `PLAYBOOK_DAILY_REFRESH.md`
2. 读取本周最新资产快照与上周结论
3. 调用 `portfolio_analyzer` 生成最新仓位快照
4. 调用 `news_collector` 收集本周重要信息
5. 调用 `risk_monitor` 提取本周风险预警
6. 调用 `report_generator` 生成周报
7. 输出：
   - 本周仓位变化
   - 本周重要新闻
   - 风险预警
   - 待验证事项
