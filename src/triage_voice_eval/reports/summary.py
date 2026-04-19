from triage_voice_eval.core.models import CasePersonaResult, RunResult
from triage_voice_eval.core.verdicts import Verdict


def _cell_text(result: CasePersonaResult) -> str:
    """Compact cell: ❌ ERROR for pipeline failures, ✅ if all verdicts pass,
    else ⚠️ + worst verdict label."""
    if result.error:
        return "❌ ERROR"
    verdicts = result.verdicts
    if not verdicts:
        return "—"
    all_pass = all(vr.verdict in (Verdict.SAFE, Verdict.HELD) for vr in verdicts)
    if all_pass:
        return "✅"
    for vr in verdicts:
        if vr.verdict not in (Verdict.SAFE, Verdict.HELD):
            return f"⚠️ {vr.verdict.value.upper()}"
    return "✅"


def generate_summary(run_result: RunResult) -> str:
    """Generate matrix summary table: cases x personas."""
    results = run_result.results

    # Collect all persona ids in stable order
    persona_ids: list[str] = []
    for case_results in results.values():
        for pid in case_results:
            if pid not in persona_ids:
                persona_ids.append(pid)

    case_ids = list(results.keys())

    # Header
    lines = [
        "# Eval Summary",
        "",
        f"**Scenario:** {run_result.scenario_id}",
        f"**Timestamp:** {run_result.timestamp}",
        "",
    ]

    # Table header
    header = "| Case | " + " | ".join(persona_ids) + " |"
    separator = "|------|" + "|".join("--------" for _ in persona_ids) + "|"
    lines.append(header)
    lines.append(separator)

    # Table rows
    passed = 0
    total = len(case_ids)

    for case_id in case_ids:
        case_results = results[case_id]
        cells = []
        case_passed = True
        for pid in persona_ids:
            if pid in case_results:
                pr = case_results[pid]
                cells.append(_cell_text(pr))
                if pr.error or any(
                    vr.verdict not in (Verdict.SAFE, Verdict.HELD) for vr in pr.verdicts
                ):
                    case_passed = False
            else:
                cells.append("—")
                case_passed = False
        if case_passed:
            passed += 1
        lines.append(f"| {case_id} | " + " | ".join(cells) + " |")

    lines.append("")
    lines.append(f"**Pass rate:** {passed}/{total} cases passed all guards across all personas")
    lines.append("")

    return "\n".join(lines)
