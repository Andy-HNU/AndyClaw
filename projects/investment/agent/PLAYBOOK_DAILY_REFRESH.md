# 数据刷新工作流

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
