# Codex 工单：Investment 稳定化（V1 -> V1.1）

## 背景
项目主链路已跑通，进入稳定化阶段。当前重点是幂等、去重、可观测性、报告契约一致性。

---

## Task A（P0）同日 risk_signal 去重与 open 收敛

### 目标
同一交易日内，`risk_signals` 不应因重复运行 workflow 而不断新增等价 open 信号。

### 约束
- 唯一性建议维度：`signal_time + signal_type + severity + message(+asset_code)`
- 重跑时应 upsert/复用或 close+reopen（策略可选，但必须幂等）

### 验收标准
1. 连续执行 3 次：
   - `persist-rebalance`
   - `monthly-review`
2. `open_risk_signals` 数量稳定，不持续增长
3. `closed_signal_count` 与策略一致且可解释

### 建议改动位置
- `src/investment_agent/db/repository.py`
- `src/investment_agent/services/rebalance_recorder.py`
- `src/investment_agent/workflows/monthly_review.py`

---

## Task B（P0）report / investment_suggestions 同日幂等策略统一

### 目标
同一日同类型报告/建议在重放中不应无限累积。

### 方案建议（二选一）
- A: upsert 同日同类型记录（保持最新）
- B: 版本化记录，但输出层默认只取 latest version

### 验收标准
1. 重复执行 `daily-review` 3 次
2. 读取当日报告时仅有一个“当前生效结果”
3. suggestions 同理可稳定读取 latest

### 建议改动位置
- `src/investment_agent/db/repository.py`
- `src/investment_agent/services/report_generator.py`
- `src/investment_agent/workflows/daily_review.py`

---

## Task C（P1）数据质量可观测性（real/fallback/mixed）

### 目标
在报告中明确当前数据来源质量，避免用户误把 fallback 当实时真值。

### 输出
在 `content_json.summary` 或新增 section 中增加：
- `data_quality`: real | fallback | mixed
- `provider_notes`: 失败源、fallback 源、时间

### 验收标准
1. 模拟主源失败时，报告显式标注 fallback
2. 主源恢复时可回到 real/mixed

### 建议改动位置
- `src/investment_agent/providers/*`
- `src/investment_agent/workflows/daily_review.py`
- `src/investment_agent/services/report_generator.py`

---

## Task D（P1）图表工件契约加固

### 目标
保证 `chart_artifacts` 契约稳定，历史不足只返回 skipped。

### 必要字段
- `status`: success | skipped | failed
- `reason`: optional（如 insufficient_history）
- `message`: 可读说明
- `path`: success 时可选

### 验收标准
1. 无历史点时：返回 skipped，不报错，不伪造图
2. 有足够历史点时：返回 success + path

### 建议改动位置
- `src/investment_agent/services/chart_artifacts.py`
- `src/investment_agent/workflows/daily_review.py`
- tests for both branches

---

## Task E（P2）内部主题码与外部基金码展示解耦

### 目标
内部 `ai/broad_index/...` 可保留用于研究映射，但对外输出统一基金全名+场外代码。

### 验收标准
1. daily/weekly/monthly 报告中不再出现主题码作为资产主标识
2. signal message 对外可读且与持仓标的一致

### 建议改动位置
- `src/investment_agent/services/signal_engine.py`
- report assembly layer

---

## 回归命令（提交前必须跑）
```bash
bash acceptance/run_v1_acceptance.sh
PYTHONPATH=src python3 -m unittest discover -s tests_python -v
```

## 交付要求
- 每个 Task 附：变更说明 + 影响面 + 回归结果
- 不改业务策略含义，仅做稳定化与契约收敛
