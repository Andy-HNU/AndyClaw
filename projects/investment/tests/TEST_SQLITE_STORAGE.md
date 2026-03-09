# 测试：SQLite 存储

## 场景
初始化数据库并写入首份资产快照。

## 输入
- `portfolio_state.json`
- `target_allocation.json`

## 预期
- 数据库创建成功
- `portfolio_assets` 至少写入 1 条记录
- `portfolio_snapshots` 至少写入 1 条记录
- 能按时间查询最近一次快照
