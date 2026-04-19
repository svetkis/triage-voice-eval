"""Minimal CLI for triage-voice-eval.

Subcommands:
    tve trend <runs_dir>       Print trend table across a directory of runs.
    tve report <result.json>   Print summary for a single run's result.json.

The CLI does not run pipelines — pipeline_fn is a Python callable, so use
``python -m your_eval`` with your own script for that.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .core.models import RunResult
from .reports import generate_summary
from .trend.analyzer import TrendAnalyzer


def _cmd_trend(args: argparse.Namespace) -> int:
    runs_dir = Path(args.runs_dir)
    if not runs_dir.is_dir():
        print(f"error: {runs_dir} is not a directory", file=sys.stderr)
        return 2
    print(TrendAnalyzer(str(runs_dir)).generate_trend_table())
    return 0


def _cmd_report(args: argparse.Namespace) -> int:
    path = Path(args.result_json)
    if not path.is_file():
        print(f"error: {path} is not a file", file=sys.stderr)
        return 2
    run = RunResult.model_validate_json(path.read_text(encoding="utf-8"))
    print(generate_summary(run))
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tve",
        description="triage-voice-eval: report and trend tools",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    trend = sub.add_parser("trend", help="print trend table across runs")
    trend.add_argument("runs_dir", help="directory containing run subdirs with result.json")
    trend.set_defaults(func=_cmd_trend)

    report = sub.add_parser("report", help="print summary for a single result.json")
    report.add_argument("result_json", help="path to a result.json file")
    report.set_defaults(func=_cmd_report)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
