from __future__ import annotations

import argparse
from pathlib import Path

from .fetcher import collect_items
from .report import render_report
from .sources import load_source_config, workspace_root


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="geopolitics_watchboard")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Collect feeds and render a markdown report.")
    run_parser.add_argument("--topic", required=True, help="Topic key from system/sources.yaml.")

    return parser


def run(topic: str) -> Path:
    config = load_source_config()
    items = collect_items(topic, config)
    report = render_report(topic, items)
    output_dir = workspace_root() / "staging" / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{topic}.md"
    output_path.write_text(report, encoding="utf-8")
    return output_path


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "run":
        output_path = run(args.topic)
        print(output_path)
        return 0
    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

