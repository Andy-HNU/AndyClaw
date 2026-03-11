from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from investment_agent.config import ProjectPaths


def render_daily_price_chart(
    paths: ProjectPaths,
    series: list[dict[str, object]],
    report_time: str,
    window_label: str = "近30次价格快照",
) -> dict[str, object]:
    if len(series) == 0:
        return {
            "status": "skipped",
            "reason": "no_series",
            "message": "no eligible asset series available for chart rendering",
        }

    valid_series = [item for item in series if len(item.get("points", [])) >= 2]
    if len(valid_series) == 0:
        return {
            "status": "skipped",
            "reason": "insufficient_history",
            "message": "need at least two price points before rendering a daily trend chart",
        }

    payload = {
        "title": f"{window_label}走势",
        "x_label": "交易日",
        "y_label": "价格/净值",
        "series": valid_series,
    }
    output_name = f"daily_trend_{str(report_time).replace(':', '-').replace(' ', '_')}.png"
    output_path = paths.report_artifacts_dir / output_name

    with tempfile.TemporaryDirectory() as td:
        input_path = Path(td) / "daily-chart.json"
        input_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        try:
            subprocess.run(
                [
                    "python3",
                    str(paths.line_chart_skill_script_path),
                    "--input",
                    str(input_path),
                    "--output",
                    str(output_path),
                    "--width",
                    "1100",
                    "--height",
                    "620",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as exc:
            return {
                "status": "failed",
                "reason": "renderer_error",
                "message": exc.stderr.strip() or exc.stdout.strip() or str(exc),
                "payload": payload,
            }

    return {
        "status": "success",
        "message": "daily trend chart generated",
        "artifact_type": "line_chart",
        "title": payload["title"],
        "series_count": len(valid_series),
        "window_label": window_label,
        "path": str(output_path),
        "payload": payload,
    }
