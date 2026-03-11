#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

PALETTE = [
    (68, 138, 255),
    (255, 99, 132),
    (75, 192, 192),
    (255, 159, 64),
    (153, 102, 255),
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
    img = Image.new("RGBA", (width, height), (11, 20, 34, 255))
    draw = ImageDraw.Draw(img)

    title_font = _load_font(34)
    label_font = _load_font(24)
    axis_font = _load_font(20)
    legend_font = _load_font(20)

    title = str(payload.get("title", "Line Chart"))
    x_label = str(payload.get("x_label", "X"))
    y_label = str(payload.get("y_label", "Y"))
    right_axis = str(payload.get("price_axis", "right")).lower() != "left"

    left = 88 if not right_axis else 52
    top, right, bottom = 84, width - 72, height - 104
    chart_w, chart_h = right - left, bottom - top

    draw.rounded_rectangle(
        (left - 14, top - 14, right + 14, bottom + 14),
        radius=16,
        fill=(14, 28, 46, 255),
        outline=(45, 70, 96, 255),
        width=2,
    )

    all_y: list[float] = []
    for s in payload["series"]:
        all_y.extend([float(pt["y"]) for pt in s["points"]])
    y_min, y_max = min(all_y), max(all_y)
    pad = (y_max - y_min) * 0.12 if y_max != y_min else 1.0
    y_min -= pad
    y_max += pad

    def to_xy(i: int, y: float, points_count: int) -> tuple[float, float]:
        x = left if points_count <= 1 else left + i * (chart_w / (points_count - 1))
        yy = top + (y_max - y) / (y_max - y_min) * chart_h
        return x, yy

    y_ticks = _nice_ticks(y_min, y_max, ticks=6)
    for tick in y_ticks:
        y = top + (y_max - tick) / (y_max - y_min) * chart_h
        draw.line([(left, y), (right, y)], fill=(50, 74, 100, 190), width=1)
        text = f"{tick:.2f}"
        if right_axis:
            draw.text((right + 10, y - 8), text, fill=(151, 176, 205, 255), font=axis_font)
        else:
            draw.text((14, y - 8), text, fill=(151, 176, 205, 255), font=axis_font)

    x_labels = [str(pt["x"]) for pt in payload["series"][0]["points"]]
    if len(x_labels) <= 8:
        tick_indexes = list(range(len(x_labels)))
    else:
        step = max(1, len(x_labels) // 6)
        tick_indexes = list(range(0, len(x_labels), step))
        if tick_indexes[-1] != len(x_labels) - 1:
            tick_indexes.append(len(x_labels) - 1)

    for idx in tick_indexes:
        x, _ = to_xy(idx, y_ticks[0], len(x_labels))
        draw.line([(x, top), (x, bottom)], fill=(33, 53, 74, 120), width=1)
        draw.text((x - 20, bottom + 8), x_labels[idx], fill=(151, 176, 205, 255), font=axis_font)

    draw.line([(left, bottom), (right, bottom)], fill=(92, 122, 156, 255), width=2)
    if right_axis:
        draw.line([(right, top), (right, bottom)], fill=(92, 122, 156, 255), width=2)
    else:
        draw.line([(left, top), (left, bottom)], fill=(92, 122, 156, 255), width=2)

    for s_idx, s in enumerate(payload["series"]):
        color = PALETTE[s_idx % len(PALETTE)]
        points = s["points"]
        path = [to_xy(i, float(pt["y"]), len(points)) for i, pt in enumerate(points)]

        # keep the area below line consistent with chart background (no white/area fill)
        draw.line([(x, y + 2) for x, y in path], fill=(0, 0, 0, 70), width=5)
        draw.line(path, fill=color + (255,), width=4)

        step = 1 if len(path) <= 12 else max(2, len(path) // 8)
        for idx, (x, y) in enumerate(path):
            if idx % step != 0 and idx != len(path) - 1:
                continue
            r = 3
            draw.ellipse((x - r, y - r, x + r, y + r), fill=(14, 28, 46, 255), outline=color + (255,), width=2)

    draw.text((left, 28), title, fill=(223, 235, 248, 255), font=title_font)
    draw.text((right - 60, bottom + 38), x_label, fill=(172, 194, 220, 255), font=label_font)
    draw.text((18, top - 28), y_label, fill=(172, 194, 220, 255), font=label_font)

    legend_x = right - 330
    legend_y = top + 8
    legend_h = max(34, 24 * len(payload["series"]) + 10)
    draw.rounded_rectangle(
        (legend_x - 12, legend_y - 6, right - 8, legend_y + legend_h),
        radius=10,
        fill=(18, 35, 56, 230),
        outline=(45, 70, 96, 255),
        width=1,
    )
    for s_idx, s in enumerate(payload["series"]):
        color = PALETTE[s_idx % len(PALETTE)]
        y = legend_y + s_idx * 24
        draw.line([(legend_x, y + 8), (legend_x + 24, y + 8)], fill=color + (255,), width=4)
        draw.text((legend_x + 30, y), str(s.get("name", f"series-{s_idx+1}")), fill=(206, 223, 242, 255), font=legend_font)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, format="PNG")
    print(str(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
