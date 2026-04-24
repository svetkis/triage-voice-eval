from ..core.models import CasePersonaResult, RunResult
from ..core.verdicts import Verdict
from ._utils import verdict_icon


def _format_verdicts(result: CasePersonaResult) -> str:
    parts = []
    for vr in result.verdicts:
        icon = verdict_icon(vr.verdict)
        parts.append(f"{icon} {vr.verdict.value.upper()} ({vr.guard_name})")
    return ", ".join(parts) if parts else "no verdicts"


def _truncate(text: str, max_len: int = 300) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len] + "…"


def _extract_response_text(response: dict) -> str:
    """Extract displayable text from the response dict."""
    if "response_text" in response:
        return str(response["response_text"])
    if "content" in response:
        return str(response["content"])
    if "text" in response:
        return str(response["text"])
    if "message" in response:
        return str(response["message"])
    return str(response) if response else ""


def generate_case_report(case_id: str, run_result: RunResult) -> str:
    """Generate markdown report for one case showing all personas side-by-side."""
    persona_results = run_result.results.get(case_id, {})

    lines = [f"# Case: {case_id}", ""]

    for persona_id, result in persona_results.items():
        lines.append(f"## {persona_id}")

        if result.error:
            lines.append(f"**❌ Error:** {result.error}")
            lines.append(f"**Latency:** {result.latency_ms:.0f}ms")
            lines.append("")
            continue

        lines.append(f"**Verdicts:** {_format_verdicts(result)}")

        # Show reason for non-passing verdicts
        for vr in result.verdicts:
            if vr.verdict not in (Verdict.SAFE, Verdict.HELD) and vr.reason:
                lines.append(f"**Reason:** {vr.reason}")
                break

        response_text = _extract_response_text(result.response)
        if response_text:
            lines.append(f"**Response:** {_truncate(response_text)}")

        lines.append(f"**Latency:** {result.latency_ms:.0f}ms")
        lines.append("")

    return "\n".join(lines)
