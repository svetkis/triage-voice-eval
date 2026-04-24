"""Tests for error rendering in reports (covers ticket #1)."""
from __future__ import annotations

from triage_voice_eval.core.models import CasePersonaResult, RunResult
from triage_voice_eval.reports import (
    generate_case_report,
    generate_persona_report,
    generate_summary,
)


def _run_with_error() -> RunResult:
    return RunResult(
        scenario_id="s1",
        results={
            "c1": {
                "p1": CasePersonaResult(
                    persona_id="p1",
                    error="RuntimeError: boom",
                    latency_ms=12.0,
                ),
            }
        },
        timestamp="2026-04-19T00:00:00+00:00",
    )


def test_summary_shows_error_cell():
    md = generate_summary(_run_with_error())
    assert "❌ ERROR" in md
    assert "0/1 cases passed" in md


def test_case_report_shows_error_and_skips_verdicts():
    md = generate_case_report("c1", _run_with_error())
    assert "❌ Error" in md
    assert "RuntimeError: boom" in md
    assert "Verdicts:" not in md


def test_persona_report_shows_error_in_cell():
    md = generate_persona_report("p1", _run_with_error())
    assert "❌ ERROR" in md
    assert "RuntimeError: boom" in md


def test_case_report_renders_response_text_as_primary_display():
    """SkyCarrier-shaped response dict is displayed as text, not as raw dict repr."""
    run = RunResult(
        scenario_id="s1",
        results={
            "c1": {
                "p1": CasePersonaResult(
                    persona_id="p1",
                    response={"response_text": "hello world"},
                    latency_ms=10.0,
                ),
            }
        },
        timestamp="2026-04-19T00:00:00+00:00",
    )
    md = generate_case_report("c1", run)
    assert "hello world" in md
    assert "{'response_text':" not in md
