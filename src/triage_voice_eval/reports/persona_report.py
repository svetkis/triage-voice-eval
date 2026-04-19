from triage_voice_eval.core.models import CasePersonaResult
from triage_voice_eval.core.verdicts import Verdict


def _verdict_icon(v: Verdict) -> str:
    return "✅" if v in (Verdict.SAFE, Verdict.HELD) else "⚠️"


def _format_verdicts_compact(result: CasePersonaResult) -> str:
    parts = []
    for vr in result.verdicts:
        icon = _verdict_icon(vr.verdict)
        label = vr.verdict.value.upper()
        if vr.verdict not in (Verdict.SAFE, Verdict.HELD) and vr.reason:
            parts.append(f"{icon} {label} ({vr.reason})")
        else:
            parts.append(f"{icon} {label}")
    return ", ".join(parts) if parts else "no verdicts"


def generate_persona_report(persona_id: str, case_results: dict[str, CasePersonaResult]) -> str:
    """Generate markdown report for one persona showing all cases."""
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
