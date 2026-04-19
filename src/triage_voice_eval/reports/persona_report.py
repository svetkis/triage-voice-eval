from ..core.models import CasePersonaResult, RunResult
from ..core.verdicts import Verdict
from ._utils import verdict_icon


def _format_verdicts_compact(result: CasePersonaResult) -> str:
    if result.error:
        return f"❌ ERROR ({result.error})"
    parts = []
    for vr in result.verdicts:
        icon = verdict_icon(vr.verdict)
        label = vr.verdict.value.upper()
        if vr.verdict not in (Verdict.SAFE, Verdict.HELD) and vr.reason:
            parts.append(f"{icon} {label} ({vr.reason})")
        else:
            parts.append(f"{icon} {label}")
    return ", ".join(parts) if parts else "no verdicts"


def generate_persona_report(persona_id: str, run_result: RunResult) -> str:
    """Generate markdown report for one persona showing all cases."""
    case_results = {
        case_id: personas[persona_id]
        for case_id, personas in run_result.results.items()
        if persona_id in personas
    }

    lines = [
        f"# Persona: {persona_id}",
        "",
        "| Case | Verdicts | Latency |",
        "|------|----------|---------|",
    ]

    for case_id, result in case_results.items():
        verdicts_str = _format_verdicts_compact(result)
        latency_str = f"{result.latency_ms:.0f}ms"
        lines.append(f"| {case_id} | {verdicts_str} | {latency_str} |")

    lines.append("")
    return "\n".join(lines)
