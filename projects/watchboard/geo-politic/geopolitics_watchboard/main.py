from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from .fetcher import collect_items
from .report import render_report
from .sources import load_source_config, load_topics_registry, topic_config, workspace_root


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="geopolitics_watchboard")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_topic = subparsers.add_parser("run-topic", help="Collect feeds and render markdown for one topic.")
    run_topic.add_argument("--topic", required=True, help="Topic key from system/topics.json")
    run_topic.add_argument("--since-hours", type=int, default=None, help="Only keep items newer than this many hours")

    run_all = subparsers.add_parser("run-all", help="Run all configured topics.")
    run_all.add_argument("--since-hours", type=int, default=None, help="Only keep items newer than this many hours")

    legacy = subparsers.add_parser("run", help="Backward-compatible alias for run-topic")
    legacy.add_argument("--topic", required=True, help="Topic key from system/topics.json")
    legacy.add_argument("--since-hours", type=int, default=None, help="Only keep items newer than this many hours")

    return parser


def output_path(topic: str, run_at: datetime) -> Path:
    date_key = run_at.strftime("%Y-%m-%d")
    ts_key = run_at.strftime("%Y%m%dT%H%M%SZ")
    return workspace_root() / "staging" / "reports" / topic / date_key / f"{ts_key}.md"


def run_topic(topic: str, since_hours: int | None = None, run_at: datetime | None = None) -> Path:
    source_cfg = load_source_config()
    registry = load_topics_registry()
    topic_cfg = topic_config(registry, topic)
    items = collect_items(topic, topic_cfg, source_cfg, since_hours=since_hours)
    report = render_report(topic, items, impact_template=topic_cfg.get("impact_template"), generated_at=run_at)

    run_time = (run_at or datetime.now(timezone.utc)).replace(microsecond=0)
    path = output_path(topic, run_time)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report, encoding="utf-8")
    return path


def run_all(since_hours: int | None = None, run_at: datetime | None = None) -> list[Path]:
    registry = load_topics_registry()
    outputs: list[Path] = []
    for topic in sorted(registry.get("topics", {})):
        outputs.append(run_topic(topic, since_hours=since_hours, run_at=run_at))
    return outputs


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command in {"run-topic", "run"}:
        print(run_topic(args.topic, since_hours=args.since_hours))
        return 0
    if args.command == "run-all":
        for path in run_all(since_hours=args.since_hours):
            print(path)
        return 0
    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
