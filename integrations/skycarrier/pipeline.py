"""pipeline_fn — wraps triage-and-voice's SkyCarrier Pipeline for the eval runner.

Flattens BotResponse into the dict shape guards expect:
- response_text, human_handoff                           → from BotResponse
- intent, emotional_state, harm_state, urgency           → from BotResponse.classification

`classification` is None only when triage itself failed; in that case the
triage-axis fields are absent from the dict, and IntentGuard/EmotionalStateGuard
report MISS rather than reading stale data.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_TRIAGE_AND_VOICE_ROOT = Path(__file__).resolve().parents[2].parent / "triage-and-voice"

from triage_voice_eval.core.models import Persona, TestCase

_pipeline = None  # lazy-initialised on first run_pipeline call — see _get_pipeline.


def _get_pipeline():
    """Build the SkyCarrier pipeline on first use.

    Kept lazy so merely importing this module (e.g. during pytest collection)
    does not require triage-and-voice to be installed or OPENAI_API_KEY to be
    set. Tests that mock run_pipeline should mock at that name.
    """
    global _pipeline
    if _pipeline is not None:
        return _pipeline

    if not _TRIAGE_AND_VOICE_ROOT.is_dir():
        raise RuntimeError(
            f"SkyCarrier eval requires the 'triage-and-voice' repository to be "
            f"a sibling of this one. Expected it at: {_TRIAGE_AND_VOICE_ROOT}. "
            f"Clone https://github.com/svetkis/triage-and-voice there and run "
            f"`pip install -e .` inside it."
        )
    if str(_TRIAGE_AND_VOICE_ROOT) not in sys.path:
        sys.path.append(str(_TRIAGE_AND_VOICE_ROOT))

    from examples.skycarrier.main import build_pipeline  # noqa: E402

    _pipeline = build_pipeline()
    return _pipeline


async def run_pipeline(case: TestCase, persona: Persona) -> dict[str, Any]:
    """Call the SkyCarrier pipeline and return a guard-readable response dict."""
    pipeline = _get_pipeline()

    from src.models import ChatMessage  # imported lazily — same sibling repo

    history = [
        ChatMessage(role=msg.get("role", "user"), content=msg["content"])
        for msg in case.history
    ]

    resp = await pipeline.process_message(case.input, history)

    result: dict[str, Any] = {
        "response_text": resp.text,
        "human_handoff": resp.human_handoff,
    }

    if resp.classification is not None:
        result["intent"] = resp.classification.intent
        result["emotional_state"] = resp.classification.user_emotional_state
        result["harm_state"] = resp.classification.harm_state
        result["urgency"] = resp.classification.urgency

    return result
