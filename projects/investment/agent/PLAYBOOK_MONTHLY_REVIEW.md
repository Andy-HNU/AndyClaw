# 月度复盘工作流

1. 执行命令：
   `PYTHONPATH=src python3 -m investment_agent.main monthly-review`
2. 检查输出中的：
   - `price_refresh`
   - `news_refresh`
   - `rebalance`
   - `monthly_plan`
   - `signal_review`
   - `report`
3. 确认报告已写入 SQLite 的 `reports`
4. 输出：
   - 当前资产比例
   - 是否触发再平衡检查
   - 本月定投建议
   - 核心风险与下月观察点
