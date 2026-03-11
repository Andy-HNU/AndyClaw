---
name: line-chart-plotter
description: Render line charts from provided timeseries data into PNG images for reports. Use when the user asks for trend charts, 7-day/30-day/90-day net value charts, or visual time-series evidence instead of text-only trend blocks.
---

# Skill: line-chart-plotter

Generate clean PNG line charts from structured data.

## Workflow
1. Prepare input JSON according to `references/input-schema.md`.
2. Run `scripts/plot_line_chart.py --input <json> --output <png>`.
3. If multiple assets are needed, either:
   - put multiple series in one chart, or
   - generate one chart per asset.
4. Attach the generated PNG in the report message.

## Output rules
- Always include chart title and axis labels.
- Keep date labels readable (auto-sampled ticks).
- Use legend when there are multiple series.
- Return warnings if points are unsorted, duplicated, or non-numeric.

## Commands
```bash
python3 scripts/plot_line_chart.py --input ./sample.json --output ./chart.png
python3 scripts/plot_line_chart.py --input ./sample.json --output ./chart.png --width 1200 --height 680
```
