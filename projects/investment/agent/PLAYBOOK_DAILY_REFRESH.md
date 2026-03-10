# 日流程工作流

## 日流程一：截图同步后的当日建议
1. 若用户先发截图：
   - 先执行 `import-snapshot`
   - 再走 `portfolio_editor`
2. 执行：
   `PYTHONPATH=src python3 -m investment_agent.main daily-review`
3. 检查输出中的：
   - `price_refresh`
   - `news_refresh`
   - `rebalance`
   - `signal_review`
   - `report`
4. 输出：
   - 今日仓位快照
   - 是否触发再平衡检查
   - 今日风险摘要
   - 今日板块新闻
   - 建议动作

## 日流程二：仅刷新行情与新闻
1. 读取数据源配置
2. 先调用主数据源获取行情
3. 再获取新闻/资讯
4. 校验字段完整性
5. 写入 SQLite
6. 若主源失败则切换备源
7. 记录刷新日志与失败原因
8. 若当前资产属于已支持类型：
   - `bond_fund`
   - `etf`
   - `index_fund`
   - `thematic_fund`
   - `commodity` 中的黄金
   则直接使用真实 provider 查询
9. 若资产类型暂不支持，则要求 OpenClaw 明确提示需要补 provider 映射或临时 fixture
