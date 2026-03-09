# Skill: portfolio_analyzer

## 目标
分析当前仓位，输出总资产、各大类占比、偏离情况、低配与高配项。

## 对应项目目的
- 管理仓位
- 风险预警
- 周报月报

## 输入
- `system/portfolio_state.json`
- `system/target_allocation.json`

## 输出
- `total_value`
- `allocation`
- `deviation`
- `underweight`
- `overweight`
- `status`

## 步骤
1. 读取资产数据
2. 按 category 聚合
3. 计算总值与占比
4. 与目标配置比较
5. 输出结构化结果

## 失败处理
- 缺少资产值：返回 `incomplete_data`
- 总资产为 0：返回 `calculation_blocked`
- 未知分类：写入 `uncategorized`
