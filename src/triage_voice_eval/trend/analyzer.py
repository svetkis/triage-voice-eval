"""TrendAnalyzer — compare eval results across runs, detect regressions."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from pydantic import BaseModel, ValidationError

from triage_voice_eval.core.models import RunResult, CasePersonaResult
from triage_voice_eval.core.verdicts import Verdict, VerdictResult

logger = logging.getLogger(__name__)

# Verdicts considered "good" (no safety issue).
_GOOD: set[Verdict] = {Verdict.SAFE, Verdict.HELD}
# Verdicts considered "bad" (safety regression).
_BAD: set[Verdict] = {Verdict.LEAK, Verdict.MISS, Verdict.BROKE}

_VERDICT_EMOJI: dict[Verdict, str] = {
    Verdict.SAFE: "✅",
    Verdict.HELD: "✅",
    Verdict.LEAK: "⚠️",
    Verdict.MISS: "⚠️",
    Verdict.BROKE: "⚠️",
}


class Regression(BaseModel):
    case_id: str
    persona_id: str
    guard_name: str
    previous_verdict: Verdict
    current_verdict: Verdict
    previous_run: str
    current_run: str


class TrendAnalyzer:
    """Analyze eval results across multiple runs."""

    def __init__(self, runs_dir: str) -> None:
        self.runs_dir = Path(runs_dir)

    def load_runs_with_stats(self) -> tuple[list[tuple[str, RunResult]], int]:
        """Load all runs from runs_dir and report how many were skipped.

        Same behavior as :meth:`load_runs`, but additionally returns the count
        of runs that were skipped due to corrupt or unreadable result files,
        so callers (e.g. the trend-table generator) can surface that count to
        users who don't have logging configured.
        """
        runs: list[tuple[str, RunResult]] = []
        skipped = 0
        for run_dir in self.runs_dir.iterdir():
            result_path = run_dir / "result.json"
            if run_dir.is_dir() and result_path.exists():
                try:
                    run_result = RunResult.model_validate_json(
                        result_path.read_text(encoding="utf-8")
                    )
                    runs.append((run_dir.name, run_result))
                except (OSError, json.JSONDecodeError, ValidationError) as exc:
                    logger.warning("Skipping %s: %s", run_dir.name, exc)
                    skipped += 1
        runs.sort(key=lambda pair: (pair[1].timestamp, pair[0]))
        return runs, skipped

    def load_runs(self) -> list[tuple[str, RunResult]]:
        """Load all runs from runs_dir, sorted by ``result.timestamp``.

        Ties (including legacy runs with empty-string timestamps, which are
        mapped to ``datetime.min`` by RunResult's validator) are broken by
        directory name for deterministic ordering.

        Corrupted or unreadable result files are skipped with a warning
        logged to ``triage_voice_eval.trend.analyzer``.
        """
        return self.load_runs_with_stats()[0]

    def detect_regressions(
        self, runs: list[tuple[str, RunResult]] | None = None
    ) -> list[Regression]:
        """Find cases where verdict worsened between consecutive runs.

        If ``runs`` is not provided, loads them via :meth:`load_runs`. Callers
        that already loaded the runs (e.g. :meth:`generate_trend_table`) should
        pass them in to avoid re-parsing every ``result.json`` twice.
        """
        if runs is None:
            runs = self.load_runs()
        if len(runs) < 2:
            return []

        regressions: list[Regression] = []

        for i in range(1, len(runs)):
            prev_name, prev_result = runs[i - 1]
            curr_name, curr_result = runs[i]

            for case_id, personas in curr_result.results.items():
                for persona_id, cpr in personas.items():
                    for vr in cpr.verdicts:
                        prev_verdict = self._find_verdict(
                            prev_result, case_id, persona_id, vr.guard_name
                        )
                        if prev_verdict is None:
                            continue
                        if prev_verdict in _GOOD and vr.verdict in _BAD:
                            regressions.append(
                                Regression(
                                    case_id=case_id,
                                    persona_id=persona_id,
                                    guard_name=vr.guard_name,
                                    previous_verdict=prev_verdict,
                                    current_verdict=vr.verdict,
                                    previous_run=prev_name,
                                    current_run=curr_name,
                                )
                            )

        return regressions

    def generate_trend_table(self) -> str:
        """Generate markdown trend table: cases x runs with verdict history."""
        runs, skipped = self.load_runs_with_stats()
        if not runs:
            return "# Trend Analysis\n\nNo runs found."

        # Collect all regressions for marking.
        regression_set: set[tuple[str, str, str, str]] = set()
        for r in self.detect_regressions(runs):
            regression_set.add((r.case_id, r.persona_id, r.guard_name, r.current_run))

        # Collect all unique (case_id, persona_id, guard_name) tuples.
        rows: set[tuple[str, str, str]] = set()
        for _, run_result in runs:
            for case_id, personas in run_result.results.items():
                for persona_id, cpr in personas.items():
                    for vr in cpr.verdicts:
                        rows.add((case_id, persona_id, vr.guard_name))

        sorted_rows = sorted(rows)
        run_names = [name for name, _ in runs]

        lines: list[str] = []
        if skipped > 0:
            lines.append(
                f"_{skipped} run(s) skipped due to errors — see warnings._"
            )
            lines.append("")
        lines.append("# Trend Analysis")
        lines.append("")

        header = "| Case | Persona | Guard | " + " | ".join(run_names) + " |"
        separator = "|------|---------|-------| " + " | ".join("---" for _ in run_names) + " |"
        lines.append(header)
        lines.append(separator)

        for case_id, persona_id, guard_name in sorted_rows:
            cells: list[str] = []
            for run_name, run_result in runs:
                verdict = self._find_verdict(run_result, case_id, persona_id, guard_name)
                if verdict is None:
                    cells.append("-")
                else:
                    emoji = _VERDICT_EMOJI[verdict]
                    cell = f"{emoji} {verdict.value.upper()}"
                    if (case_id, persona_id, guard_name, run_name) in regression_set:
                        cell += " ←"
                    cells.append(cell)
            line = f"| {case_id} | {persona_id} | {guard_name} | " + " | ".join(cells) + " |"
            lines.append(line)

        return "\n".join(lines)

    @staticmethod
    def _find_verdict(
        run_result: RunResult,
        case_id: str,
        persona_id: str,
        guard_name: str,
    ) -> Verdict | None:
        """Find a specific verdict in a run result."""
        personas = run_result.results.get(case_id)
        if not personas:
            return None
        cpr = personas.get(persona_id)
        if not cpr:
            return None
        for vr in cpr.verdicts:
            if vr.guard_name == guard_name:
                return vr.verdict
        return None
