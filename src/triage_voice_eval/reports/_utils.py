from ..core.verdicts import Verdict


def verdict_icon(v: Verdict) -> str:
    """Return emoji icon for a verdict: pass or fail."""
    return "✅" if v in (Verdict.SAFE, Verdict.HELD) else "⚠️"
