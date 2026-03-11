# Input schema for plot_line_chart.py

Use UTF-8 JSON.

## Structure

```json
{
  "title": "近7个交易日净值走势",
  "x_label": "交易日",
  "y_label": "单位净值",
  "series": [
    {
      "name": "易方达人工智能ETF联接C(012734)",
      "points": [
        {"x": "03-02", "y": 1.8391},
        {"x": "03-03", "y": 1.7671}
      ]
    }
  ]
}
```

## Notes
- `series` must contain at least one item.
- each series must contain at least two points.
- `y` must be numeric.
- `x` can be string/date/number (display label).
- x positions are rendered in provided order (no date parser required).
