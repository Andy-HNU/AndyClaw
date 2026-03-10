# Skill: portfolio_editor

## 目标
通过自然语言驱动持仓对象的新增、修改、删除与校验，安全更新
`system/portfolio_state.json` 与相关持仓字段。

## 适用场景
- 用户说“我新买了一只基金”
- 用户说“把这只基金加到仓位里”
- 用户说“这只基金的份额/金额/成本更新一下”
- 用户说“这只资产从仓里删掉”
- 用户说“把这只资产改成 ETF / 债基 / 黄金 / 现金”

## 对应项目目的
- 管理仓位
- 风险预警
- 周报月报

## 输入
- 用户提供的资产信息，尽量包含：
  - 名称
  - `category`
  - `asset_type`
  - `symbol`
  - `value`
  - `shares`
  - `average_cost`
  - 可选 `theme`

## 输出
- 结构化持仓对象
- 更新后的 `portfolio_state.json`
- 缺失字段清单
- 对当前 provider 支持情况的说明

## 支持类型
当前建议优先支持：
- `bond_fund`
- `etf`
- `index_fund`
- `thematic_fund`
- `commodity` 中的黄金
- `cash`

若用户给出的资产不属于以上类型：
- 不要假装“已经支持自动查询”
- 应明确标记为：
  - `unsupported_asset_type`
  - 需要补 provider 映射或临时 fixture

## 步骤
1. 先识别用户动作：
   - `add`
   - `update`
   - `remove`
2. 把自然语言解析为持仓对象字段
3. 检查是否缺少关键字段：
   - `category`
   - `asset_type`
   - `symbol`
   - `value`
   - `shares`
4. 若字段完整，则写回 `system/portfolio_state.json`
5. 写回后提示：
   - 当前类型是否能被真实 provider 直接查询
   - 若能，则后续可直接执行 `refresh-prices` / `weekly-review` / `monthly-review`
   - 若不能，则需要补 provider 支持

## 字段约定
- `category` 只负责永久组合大类：
  - `stock`
  - `bond`
  - `gold`
  - `cash`
- `asset_type` 负责更细的查询和分析类型：
  - `bond_fund`
  - `etf`
  - `index_fund`
  - `thematic_fund`
  - `commodity`
  - `cash`
- `symbol` 必须尽量使用真实 provider 能识别的代码

## 失败处理
- 若缺少关键字段：返回缺失字段，不直接写文件
- 若 `asset_type` 不支持：允许写入，但要明确标记“当前无法直接查询真实行情”
- 若用户只说“加一只基金”但没给代码和类型：先要求补充，不猜

## 与代码层的边界
- 本 skill 负责把自然语言变成结构化持仓对象并安全落到 JSON
- provider 是否能真实查询，由代码层决定
- 若新增类型反复出现，应升级为：
  - 扩展 provider
  - 扩展信号与报告逻辑
  - 扩展测试样本
