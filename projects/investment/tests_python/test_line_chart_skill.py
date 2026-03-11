from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


class LineChartSkillTests(unittest.TestCase):
    def test_plot_line_chart_generates_png(self) -> None:
        skill_dir = Path(__file__).resolve().parents[1] / "skills" / "line-chart-plotter"
        script = skill_dir / "scripts" / "plot_line_chart.py"

        payload = {
            "title": "7日净值走势",
            "x_label": "交易日",
            "y_label": "单位净值",
            "series": [
                {
                    "name": "易方达人工智能ETF联接C(012734)",
                    "points": [
                        {"x": "03-02", "y": 1.8391},
                        {"x": "03-03", "y": 1.7671},
                        {"x": "03-04", "y": 1.7417},
                        {"x": "03-05", "y": 1.7821},
                        {"x": "03-06", "y": 1.7849},
                        {"x": "03-09", "y": 1.7724},
                        {"x": "03-10", "y": 1.8072},
                    ],
                }
            ],
        }

        with tempfile.TemporaryDirectory() as td:
            input_path = Path(td) / "chart-input.json"
            output_path = Path(td) / "chart-output.png"
            input_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

            subprocess.run(
                [
                    "python3",
                    str(script),
                    "--input",
                    str(input_path),
                    "--output",
                    str(output_path),
                    "--width",
                    "900",
                    "--height",
                    "520",
                ],
                check=True,
            )

            self.assertTrue(output_path.exists())
            self.assertGreater(output_path.stat().st_size, 1024)

            with output_path.open("rb") as fh:
                self.assertEqual(fh.read(8), b"\x89PNG\r\n\x1a\n")


if __name__ == "__main__":
    unittest.main()
