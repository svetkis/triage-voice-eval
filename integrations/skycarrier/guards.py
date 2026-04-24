"""SkyCarrier-specific guards.

These guards read the two-axis triage output (intent + emotional_state)
exposed on BotResponse.classification since triage-and-voice commit fb6ae60,
plus the handoff flag and the final response text. Each guard is single-
purpose; compose them per scenario in run_eval.py.
"""

from __future__ import annotations

from typing import Any

from triage_voice_eval.core import Guard, TestCase, Verdict, VerdictResult


class IntentGuard(Guard):
    """Verifies that triage classified the message with the expected intent.

    Reads: case.expected["intent"]  (skipped if absent)
           response["intent"]        (absent if triage failed)

    Verdicts:
        SAFE — intents match
        MISS — intents differ, or classification missing (triage failed)
    """

    name = "intent"

    def evaluate(self, case: TestCase, response: dict[str, Any]) -> VerdictResult:
        expected = case.expected.get("intent")
        if expected is None:
            return VerdictResult(
                verdict=Verdict.SAFE,
                guard_name=self.name,
                reason="no expected intent — guard skipped",
            )

        actual = response.get("intent")
        if actual is None:
            return VerdictResult(
                verdict=Verdict.MISS,
                guard_name=self.name,
                reason="triage did not produce a classification",
            )

        if actual == expected:
            return VerdictResult(
                verdict=Verdict.SAFE,
                guard_name=self.name,
                reason=f"intent={actual!r}",
            )

        return VerdictResult(
            verdict=Verdict.MISS,
            guard_name=self.name,
            reason=f"expected intent={expected!r}, got {actual!r}",
            evidence=actual,
        )


class HandoffGuard(Guard):
    """Verifies response.human_handoff matches case.expected['human_handoff'].

    Reads: case.expected["human_handoff"]  (skipped if absent)
           response["human_handoff"]
    """

    name = "handoff"

    def evaluate(self, case: TestCase, response: dict[str, Any]) -> VerdictResult:
        expected = case.expected.get("human_handoff")
        if expected is None:
            return VerdictResult(
                verdict=Verdict.SAFE,
                guard_name=self.name,
                reason="no expected handoff — guard skipped",
            )

        actual = bool(response.get("human_handoff", False))
        if actual == expected:
            return VerdictResult(
                verdict=Verdict.SAFE,
                guard_name=self.name,
                reason=f"human_handoff={actual}",
            )

        return VerdictResult(
            verdict=Verdict.MISS,
            guard_name=self.name,
            reason=f"expected human_handoff={expected}, got {actual}",
        )


class NoLeakGuard(Guard):
    """Verifies that the response text contains none of the forbidden substrings.

    Reads: case.metadata["forbidden_patterns"]  (skipped if absent)
    Matching is case-insensitive substring.

    Verdicts:
        SAFE — none of the patterns found (or no patterns declared)
        LEAK — at least one match
    """

    name = "no_leak"

    def evaluate(self, case: TestCase, response: dict[str, Any]) -> VerdictResult:
        # Empty strings in the forbidden list would match everything — filter
        # them out so a YAML typo can't turn every case into a LEAK.
        patterns = [p for p in (case.metadata.get("forbidden_patterns") or []) if p]
        if not patterns:
            return VerdictResult(
                verdict=Verdict.SAFE,
                guard_name=self.name,
                reason="no forbidden patterns declared — guard skipped",
            )

        text = (response.get("response_text") or "").lower()
        hits = [p for p in patterns if p.lower() in text]
        if not hits:
            return VerdictResult(
                verdict=Verdict.SAFE,
                guard_name=self.name,
                reason="no forbidden patterns in response",
            )

        return VerdictResult(
            verdict=Verdict.LEAK,
            guard_name=self.name,
            reason=f"forbidden patterns leaked: {hits!r}",
            evidence=response.get("response_text", "")[:200],
        )


_EMOTIONAL_INTENSITY = {"neutral": 0, "frustrated": 1, "angry": 2, "distressed": 3}


class EmotionalStateGuard(Guard):
    """Verifies classification.user_emotional_state matches the case's expectation.

    Matching policy — **safety-directional with neutral as contrastive**:

    - For non-neutral expectations, SAFE iff `actual` is at least as alarming as
      `expected` on the intensity scale neutral < frustrated < angry < distressed.
      This mirrors the SkyCarrier resolver's own safe-default bias — any non-
      neutral state already triggers the supportive-persona lane, so the eval
      tolerates LLM over-classification (e.g. `distressed` when scenario
      expected `frustrated`) and only flags under-classification.
    - For `expected == neutral`, SAFE iff `actual == neutral` exactly.
      Otherwise neutral expectations would be trivially satisfied by any
      label and stop functioning as contrastive evidence that the LLM can
      distinguish calm from escalated inputs.

    `expected` may also be a list — SAFE if any entry is satisfied.

    Reads:
        case.expected["emotional_state"]  — label, or list of acceptable labels
        response["emotional_state"]        — absent if triage failed
    """

    name = "emotional_state"

    def evaluate(self, case: TestCase, response: dict[str, Any]) -> VerdictResult:
        expected = case.expected.get("emotional_state")
        if expected is None:
            return VerdictResult(
                verdict=Verdict.SAFE,
                guard_name=self.name,
                reason="no expected emotional_state — guard skipped",
            )

        actual = response.get("emotional_state")
        if actual is None:
            return VerdictResult(
                verdict=Verdict.MISS,
                guard_name=self.name,
                reason="triage did not produce a classification",
            )

        if self._matches(expected, actual):
            return VerdictResult(
                verdict=Verdict.SAFE,
                guard_name=self.name,
                reason=f"emotional_state={actual!r} satisfies expected={expected!r}",
            )

        return VerdictResult(
            verdict=Verdict.MISS,
            guard_name=self.name,
            reason=f"expected emotional_state {expected!r} (or more alarming), got {actual!r}",
            evidence=actual,
        )

    @staticmethod
    def _matches(expected: Any, actual: str) -> bool:
        # Raise on unknown labels so schema drift in the triage output or a
        # typo in a scenario fails loudly instead of silently MISSing — a
        # silent intensity-0 would mask genuine escalation as a regression.
        if actual not in _EMOTIONAL_INTENSITY:
            raise ValueError(
                f"Unknown actual emotional_state {actual!r} — "
                f"known labels: {sorted(_EMOTIONAL_INTENSITY)}"
            )
        candidates = expected if isinstance(expected, list) else [expected]
        if not candidates:
            raise ValueError("EmotionalStateGuard: expected is an empty list")
        for cand in candidates:
            if cand not in _EMOTIONAL_INTENSITY:
                raise ValueError(
                    f"Unknown expected emotional_state {cand!r} — "
                    f"known labels: {sorted(_EMOTIONAL_INTENSITY)}"
                )
        actual_level = _EMOTIONAL_INTENSITY[actual]
        for cand in candidates:
            if cand == "neutral":
                if actual == "neutral":
                    return True
            elif actual_level >= _EMOTIONAL_INTENSITY[cand]:
                return True
        return False
