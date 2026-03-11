#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

PALETTE = [
    (52, 152, 219),
    (231, 76, 60),
    (46, 204, 113),
    (155, 89, 182),
    (241, 196, 15),
    (230, 126, 34),
    (26, 188, 156),
]


def _load_font(size: int) -> ImageFont.ImageFont:
    for candidate in [
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]:
        p = Path(candidate)
        if p.exists():
            return ImageFont.truetype(str(p), size=size)
    return ImageFont.load_default()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render line chart PNG from JSON input")
    parser.add_argument("--input", required=True, help="Input JSON path")
    parser.add_argument("--output", required=True, help="Output PNG path")
    parser.add_argument("--width", type=int, default=1100)
    parser.add_argument("--height", type=int, default=620)
    return parser.parse_args()


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    series = payload.get("series")
    if not isinstance(series, list) or not series:
        errors.append("`series` must be a non-empty list")
        return errors

    for idx, s in enumerate(series):
        if not isinstance(s, dict):
            errors.append(f"series[{idx}] must be an object")
            continue
        points = s.get("points")
        if not isinstance(points, list) or len(points) < 2:
            errors.append(f"series[{idx}].points must have at least 2 points")
            continue
        for j, pt in enumerate(points):
            if not isinstance(pt, dict):
                errors.append(f"series[{idx}].points[{j}] must be an object")
                continue
            if "x" not in pt:
                errors.append(f"series[{idx}].points[{j}] missing x")
            y = pt.get("y")
            if not isinstance(y, (int, float)):
                errors.append(f"series[{idx}].points[{j}].y must be numeric")
    return errors


def _nice_ticks(y_min: float, y_max: float, ticks: int = 6) -> list[float]:
    if y_max == y_min:
        return [y_min + i for i in range(ticks)]
    step = (y_max - y_min) / (ticks - 1)
    return [y_min + i * step for i in range(ticks)]


def main() -> int:
    args = parse_args()
    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    errors = validate_payload(payload)
    if errors:
        raise SystemExit("Input validation failed:\n- " + "\n- ".join(errors))

    width, height = args.width, args.height
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)

    title_font = _load_font(28)
    label_font = _load_font(19)
    axis_font = _load_font(16)
    legend_font = _load_font(15)

    title = str(payload.get("title", "Line Chart"))
    x_label = str(payload.get("x_label", "X"))
    y_label = str(payload.get("y_label", "Y"))

    left, top, right, bottom = 100, 90, width - 70, height - 100
    chart_w, chart_h = right - left, bottom - top

    # Gather y range across all series
    all_y: list[float] = []
    max_points = 0
    for s in payload["series"]:
        ys = [float(pt["y"]) for pt in s["points"]]
        all_y.extend(ys)
        max_points = max(max_points, len(ys))
    y_min, y_max = min(all_y), max(all_y)
    pad = (y_max - y_min) * 0.08 if y_max != y_min else 1.0
    y_min -= pad
    y_max += pad

    def to_xy(i: int, y: float, points_count: int) -> tuple[float, float]:
        x = left if points_count <= 1 else left + i * (chart_w / (points_count - 1))
        yy = top + (y_max - y) / (y_max - y_min) * chart_h
        return x, yy

    # Grid + y ticks
    y_ticks = _nice_ticks(y_min, y_max, ticks=6)
    for tick in y_ticks:
        y = top + (y_max - tick) / (y_max - y_min) * chart_h
        draw.line([(left, y), (right, y)], fill=(230, 230, 230), width=1)
        draw.text((20, y - 9), f"{tick:.2f}", fill=(90, 90, 90), font=axis_font)

    # Axes
    draw.line([(left, top), (left, bottom)], fill=(80, 80, 80), width=2)
    draw.line([(left, bottom), (right, bottom)], fill=(80, 80, 80), width=2)

    # X ticks based on first series labels (sampled)
    x_labels = [str(pt["x"]) for pt in payload["series"][0]["points"]]
    if len(x_labels) <= 10:
        tick_indexes = list(range(len(x_labels)))
    else:
        step = max(1, len(x_labels) // 8)
        tick_indexes = list(range(0, len(x_labels), step))
        if tick_indexes[-1] != len(x_labels) - 1:
            tick_indexes.append(len(x_labels) - 1)

    for idx in tick_indexes:
        x, _ = to_xy(idx, y_ticks[0], len(x_labels))
        draw.line([(x, bottom), (x, bottom + 5)], fill=(80, 80, 80), width=1)
        draw.text((x - 18, bottom + 10), x_labels[idx], fill=(90, 90, 90), font=axis_font)

    # Plot series
    for s_idx, s in enumerate(payload["series"]):
        color = PALETTE[s_idx % len(PALETTE)]
        points = s["points"]
        path = [to_xy(i, float(pt["y"]), len(points)) for i, pt in enumerate(points)]
        draw.line(path, fill=color, width=3)
        for x, y in path:
            r = 3
            draw.ellipse((x - r, y - r, x + r, y + r), fill=color)

    # Title and labels
    draw.text((left, 30), title, fill=(20, 20, 20), font=title_font)
    draw.text((right - 60, bottom + 45), x_label, fill=(70, 70, 70), font=label_font)
    draw.text((20, top - 30), y_label, fill=(70, 70, 70), font=label_font)

    # Legend
    legend_x = right - 320
    legend_y = top + 10
    for s_idx, s in enumerate(payload["series"]):
        color = PALETTE[s_idx % len(PALETTE)]
        y = legend_y + s_idx * 24
        draw.line([(legend_x, y + 8), (legend_x + 24, y + 8)], fill=color, width=3)
        draw.text((legend_x + 30, y), str(s.get("name", f"series-{s_idx+1}")), fill=(60, 60, 60), font=legend_font)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, format="PNG")
    print(str(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
