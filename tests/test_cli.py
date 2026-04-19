"""Tests for the tve CLI."""
from __future__ import annotations

from datetime import datetime, timezone

from triage_voice_eval.cli import main
from triage_voice_eval.core.models import (
    CasePersonaResult,
    RunResult,
)
from triage_voice_eval.core.verdicts import Verdict, VerdictResult


def _sample_run() -> RunResult:
    return RunResult(
        scenario_id="s1",
        results={
            "c1": {
                "p1": CasePersonaResult(
                    persona_id="p1",
                    verdicts=[
                        VerdictResult(
                            verdict=Verdict.SAFE,
                            guard_name="crisis",
                            reason="ok",
                        )
                    ],
                )
            }
        },
        timestamp=datetime(2026, 4, 19, tzinfo=timezone.utc),
    )


def test_cli_report_prints_summary(tmp_path, capsys):
    f = tmp_path / "result.json"
    f.write_text(_sample_run().model_dump_json(), encoding="utf-8")

    exit_code = main(["report", str(f)])

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "Eval Summary" in out
    assert "s1" in out
    assert "✅" in out


def test_cli_trend_prints_table(tmp_path, capsys):
    run_dir = tmp_path / "run-001"
    run_dir.mkdir()
    (run_dir / "result.json").write_text(
        _sample_run().model_dump_json(), encoding="utf-8"
    )

    exit_code = main(["trend", str(tmp_path)])

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "Trend Analysis" in out
    assert "run-001" in out


def test_cli_report_missing_file_exits_2(tmp_path, capsys):
    exit_code = main(["report", str(tmp_path / "nope.json")])
    assert exit_code == 2
    err = capsys.readouterr().err
    assert "is not a file" in err


def test_cli_trend_missing_dir_exits_2(tmp_path, capsys):
    exit_code = main(["trend", str(tmp_path / "nope")])
    assert exit_code == 2
    err = capsys.readouterr().err
    assert "is not a directory" in err
