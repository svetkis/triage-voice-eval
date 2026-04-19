"""Tests for TrendAnalyzer — regression detection and trend tables."""

from __future__ import annotations

import json

import pytest

from triage_voice_eval.core.models import CasePersonaResult, RunResult
from triage_voice_eval.core.verdicts import Verdict, VerdictResult
from triage_voice_eval.trend.analyzer import Regression, TrendAnalyzer


def _make_run(
    scenario_id: str,
    cases: dict[str, dict[str, list[tuple[str, Verdict]]]],
    timestamp: str = "",
) -> RunResult:
    """Build a RunResult from a compact spec.

    cases: {case_id: {persona_id: [(guard_name, verdict), ...]}}
    """
    results: dict[str, dict[str, CasePersonaResult]] = {}
    for case_id, personas in cases.items():
        results[case_id] = {}
        for persona_id, guard_verdicts in personas.items():
            results[case_id][persona_id] = CasePersonaResult(
                persona_id=persona_id,
                verdicts=[
                    VerdictResult(verdict=v, guard_name=g, reason="test")
                    for g, v in guard_verdicts
                ],
            )
    return RunResult(scenario_id=scenario_id, results=results, timestamp=timestamp)


def _save_run(tmp_path, run_name: str, run_result: RunResult) -> None:
    run_dir = tmp_path / run_name
    run_dir.mkdir()
    (run_dir / "result.json").write_text(run_result.model_dump_json())


def test_detect_regression(tmp_path):
    """Create two runs where verdict worsens -> regression detected."""
    run1 = _make_run("s1", {"case-1": {"persona-1": [("crisis", Verdict.SAFE)]}})
    run2 = _make_run("s1", {"case-1": {"persona-1": [("crisis", Verdict.LEAK)]}})

    _save_run(tmp_path, "run-20240101-120000", run1)
    _save_run(tmp_path, "run-20240102-120000", run2)

    analyzer = TrendAnalyzer(str(tmp_path))
    regressions = analyzer.detect_regressions()

    assert len(regressions) == 1
    r = regressions[0]
    assert r.case_id == "case-1"
    assert r.persona_id == "persona-1"
    assert r.guard_name == "crisis"
    assert r.previous_verdict == Verdict.SAFE
    assert r.current_verdict == Verdict.LEAK
    assert r.previous_run == "run-20240101-120000"
    assert r.current_run == "run-20240102-120000"


def test_no_regression(tmp_path):
    """Two runs with same verdict -> no regression."""
    run1 = _make_run("s1", {"case-1": {"persona-1": [("crisis", Verdict.SAFE)]}})
    run2 = _make_run("s1", {"case-1": {"persona-1": [("crisis", Verdict.SAFE)]}})

    _save_run(tmp_path, "run-20240101-120000", run1)
    _save_run(tmp_path, "run-20240102-120000", run2)

    analyzer = TrendAnalyzer(str(tmp_path))
    regressions = analyzer.detect_regressions()

    assert len(regressions) == 0


def test_regression_held_to_broke(tmp_path):
    """HELD -> BROKE is a regression."""
    run1 = _make_run("s1", {"case-1": {"persona-1": [("jailbreak", Verdict.HELD)]}})
    run2 = _make_run("s1", {"case-1": {"persona-1": [("jailbreak", Verdict.BROKE)]}})

    _save_run(tmp_path, "run-20240101-120000", run1)
    _save_run(tmp_path, "run-20240102-120000", run2)

    analyzer = TrendAnalyzer(str(tmp_path))
    regressions = analyzer.detect_regressions()

    assert len(regressions) == 1
    assert regressions[0].previous_verdict == Verdict.HELD
    assert regressions[0].current_verdict == Verdict.BROKE


def test_improvement_not_regression(tmp_path):
    """LEAK -> SAFE is an improvement, not a regression."""
    run1 = _make_run("s1", {"case-1": {"persona-1": [("crisis", Verdict.LEAK)]}})
    run2 = _make_run("s1", {"case-1": {"persona-1": [("crisis", Verdict.SAFE)]}})

    _save_run(tmp_path, "run-20240101-120000", run1)
    _save_run(tmp_path, "run-20240102-120000", run2)

    analyzer = TrendAnalyzer(str(tmp_path))
    regressions = analyzer.detect_regressions()

    assert len(regressions) == 0


def test_trend_table_format(tmp_path):
    """Verify markdown table is generated correctly."""
    run1 = _make_run("s1", {"case-1": {"persona-1": [("crisis", Verdict.SAFE)]}})
    run2 = _make_run("s1", {"case-1": {"persona-1": [("crisis", Verdict.SAFE)]}})
    run3 = _make_run("s1", {"case-1": {"persona-1": [("crisis", Verdict.LEAK)]}})

    _save_run(tmp_path, "run-001", run1)
    _save_run(tmp_path, "run-002", run2)
    _save_run(tmp_path, "run-003", run3)

    analyzer = TrendAnalyzer(str(tmp_path))
    table = analyzer.generate_trend_table()

    assert "# Trend Analysis" in table
    assert "| Case | Persona | Guard |" in table
    assert "run-001" in table
    assert "run-002" in table
    assert "run-003" in table
    assert "SAFE" in table
    assert "LEAK" in table
    # The regression marker
    assert "←" in table


def test_load_runs_sorts_by_timestamp_not_dirname(tmp_path):
    """Sorting uses result.timestamp first, so arbitrarily-named dirs still order correctly."""
    from datetime import datetime, timezone

    older = _make_run("s1", {"c1": {"p1": [("crisis", Verdict.SAFE)]}})
    older.timestamp = datetime(2024, 1, 1, tzinfo=timezone.utc)
    newer = _make_run("s1", {"c1": {"p1": [("crisis", Verdict.HELD)]}})
    newer.timestamp = datetime(2024, 6, 1, tzinfo=timezone.utc)

    # Dir names are intentionally out of chronological order.
    _save_run(tmp_path, "zzz-first-by-name-but-newer", newer)
    _save_run(tmp_path, "aaa-last-by-name-but-older", older)

    analyzer = TrendAnalyzer(str(tmp_path))
    runs = analyzer.load_runs()

    assert [name for name, _ in runs] == [
        "aaa-last-by-name-but-older",
        "zzz-first-by-name-but-newer",
    ]


def test_load_runs_skips_corrupt_files_and_logs(tmp_path, caplog):
    """Corrupt result.json is skipped with a warning, not raised."""
    import logging

    good = _make_run("s1", {"case-1": {"persona-1": [("crisis", Verdict.SAFE)]}})
    _save_run(tmp_path, "run-001", good)

    bad_dir = tmp_path / "run-002"
    bad_dir.mkdir()
    (bad_dir / "result.json").write_text("{not valid json")

    analyzer = TrendAnalyzer(str(tmp_path))
    with caplog.at_level(logging.WARNING, logger="triage_voice_eval.trend.analyzer"):
        runs = analyzer.load_runs()

    assert len(runs) == 1
    assert runs[0][0] == "run-001"
    assert any("run-002" in rec.message for rec in caplog.records)


def test_load_runs_sorted(tmp_path):
    """Runs are loaded sorted by directory name (timestamp)."""
    run_b = _make_run("s1", {"case-1": {"persona-1": [("crisis", Verdict.SAFE)]}})
    run_a = _make_run("s1", {"case-1": {"persona-1": [("crisis", Verdict.HELD)]}})

    _save_run(tmp_path, "run-20240201-120000", run_b)
    _save_run(tmp_path, "run-20240101-120000", run_a)

    analyzer = TrendAnalyzer(str(tmp_path))
    runs = analyzer.load_runs()

    assert runs[0][0] == "run-20240101-120000"
    assert runs[1][0] == "run-20240201-120000"
