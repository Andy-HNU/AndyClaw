# 周报工作流

1. 执行命令：
   `PYTHONPATH=src python3 -m investment_agent.main weekly-review`
2. 检查输出中的：
   - `price_refresh`
   - `news_refresh`
   - `signal_review`
   - `report`
3. 确认 `reports` 表中出现 `weekly` 类型报告
4. 输出：
   - 本周仓位变化
   - 本周重要新闻
   - 风险预警
   - 待验证事项
