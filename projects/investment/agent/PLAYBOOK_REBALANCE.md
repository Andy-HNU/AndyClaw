# 再平衡检查工作流

1. 读取 `../system/target_allocation.json`
2. 读取 SQLite 中最新仓位分析
3. 若仓位分析不存在，则先调用 `portfolio_analyzer`
4. 调用 `rebalancing_engine` 判断偏离是否超过阈值
5. 若未超过阈值：输出继续观察
6. 若超过阈值：先给出用新增资金修正的方案
7. 仅在偏离显著且新增资金不足时，补充卖出讨论方案
8. 写入再平衡结果与执行建议
