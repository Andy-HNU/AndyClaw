---
name: policy-news-analysis
description: Analyze policy documents and current affairs for decision signals using a seven-step framework plus pre-analysis knowledge diagnosis. Use when users ask for policy/event interpretation, impact analysis, decision implications, or action-oriented briefings (not plain summaries). Supports audience-specific analysis (investor/industry/operator/research), anomaly-first reasoning, and post-analysis SQLite knowledge sedimentation.
---

# Policy Analysis Skill

1. Confirm audience before reading deeply. Ask: investor, industry practitioner, business operator, or researcher/media.
2. Run Step 0 first: identify domain tags and knowledge-gap hypotheses.
3. Query SQLite knowledge base directionally (no full-table scan):
   - `domain_knowledge` for structural facts
   - `historical_reference` for analogs
   - `current_state` for current context
4. Execute seven-step workflow in order:
   - Step 1 anomaly scan
   - Step 2 self-explanation from source material
   - Step 3 external explanation of anomalies
   - Step 4 priority from ordering/structure
   - Step 5 logic-closure subtraction
   - Step 6 changed vs unchanged
   - Step 7 global external calibration
5. Output action-oriented analysis instead of summary.
6. Always mark uncertainty with `[待验证]` and missing critical facts with `[知识缺口]`.
7. After each analysis, output a knowledge sedimentation package and write it into SQLite via bundled script.

## Output skeleton

Use this exact section order:

1. 核心信号摘要（<=3句）
2. 信号来源（异常点 + 结构变化）
3. 核心逻辑链（信号→定性/根因→行动/传导→工具/影响）
4. 值得深挖的2-3个关键点（含行动意义）
5. 延续未变部分（简要）
6. 知识缺口与待验证事项
7. 知识沉淀包（domain/historical/current_state）

## Resources

- Framework reference: `references/openclaw_policy_analysis_framework.md`
- SQL schema + DB init: `scripts/init_policy_kb.py`
- Minimal writer: `scripts/write_policy_knowledge.py`

## Run commands

```bash
python3 skills/policy-news-analysis/scripts/init_policy_kb.py --db memory/policy_knowledge.db
python3 skills/policy-news-analysis/scripts/write_policy_knowledge.py --db memory/policy_knowledge.db --input /tmp/sediment.json
```
