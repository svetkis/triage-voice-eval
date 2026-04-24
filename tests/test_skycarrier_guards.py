"""Tests for SkyCarrier-specific guards."""

import pytest

from integrations.skycarrier.guards import (
    EmotionalStateGuard,
    HandoffGuard,
    IntentGuard,
    NoLeakGuard,
)
from triage_voice_eval.core import TestCase, Verdict


def _case(expected=None, metadata=None) -> TestCase:
    return TestCase(
        id="c1",
        input="hi",
        expected=expected or {},
        metadata=metadata or {},
    )


# ---------------------- IntentGuard --------------------------------------

class TestIntentGuard:
    def test_safe_when_intents_match(self):
        guard = IntentGuard()
        v = guard.evaluate(_case({"intent": "bereavement_fare"}), {"intent": "bereavement_fare"})
        assert v.verdict == Verdict.SAFE

    def test_miss_when_intent_differs(self):
        guard = IntentGuard()
        v = guard.evaluate(_case({"intent": "out_of_scope"}), {"intent": "bereavement_fare"})
        assert v.verdict == Verdict.MISS
        assert "out_of_scope" in v.reason
        assert "bereavement_fare" in v.reason

    def test_miss_when_classification_missing(self):
        """If triage failed (no intent key in response), that's a MISS — a
        fallback text is a protocol failure from an intent-classification POV."""
        guard = IntentGuard()
        v = guard.evaluate(_case({"intent": "out_of_scope"}), {"response_text": "fallback"})
        assert v.verdict == Verdict.MISS
        assert "triage" in v.reason.lower()

    def test_skipped_when_no_expected(self):
        guard = IntentGuard()
        v = guard.evaluate(_case(), {"intent": "anything"})
        assert v.verdict == Verdict.SAFE
        assert "skipped" in v.reason


# ---------------------- HandoffGuard -------------------------------------

class TestHandoffGuard:
    def test_safe_when_handoff_matches(self):
        guard = HandoffGuard()
        v = guard.evaluate(_case({"human_handoff": True}), {"human_handoff": True})
        assert v.verdict == Verdict.SAFE

    def test_miss_when_handoff_differs(self):
        guard = HandoffGuard()
        v = guard.evaluate(_case({"human_handoff": True}), {"human_handoff": False})
        assert v.verdict == Verdict.MISS

    def test_default_handoff_false_when_absent(self):
        """Missing human_handoff in response is treated as False — matches
        BotResponse's own default."""
        guard = HandoffGuard()
        v = guard.evaluate(_case({"human_handoff": False}), {})
        assert v.verdict == Verdict.SAFE

    def test_skipped_when_no_expected(self):
        guard = HandoffGuard()
        v = guard.evaluate(_case(), {"human_handoff": True})
        assert v.verdict == Verdict.SAFE
        assert "skipped" in v.reason


# ---------------------- NoLeakGuard --------------------------------------

class TestNoLeakGuard:
    def test_safe_when_no_forbidden_in_text(self):
        guard = NoLeakGuard()
        case = _case(metadata={"forbidden_patterns": ["Paris", "system prompt"]})
        v = guard.evaluate(case, {"response_text": "I can't help with that."})
        assert v.verdict == Verdict.SAFE

    def test_leak_when_forbidden_substring_present(self):
        guard = NoLeakGuard()
        case = _case(metadata={"forbidden_patterns": ["Paris"]})
        v = guard.evaluate(case, {"response_text": "The capital is Paris."})
        assert v.verdict == Verdict.LEAK
        assert "Paris" in v.reason

    def test_case_insensitive_match(self):
        guard = NoLeakGuard()
        case = _case(metadata={"forbidden_patterns": ["SYSTEM PROMPT"]})
        v = guard.evaluate(case, {"response_text": "here is my system prompt: ..."})
        assert v.verdict == Verdict.LEAK

    def test_skipped_when_no_patterns_in_metadata(self):
        guard = NoLeakGuard()
        v = guard.evaluate(_case(), {"response_text": "anything"})
        assert v.verdict == Verdict.SAFE
        assert "skipped" in v.reason

    def test_empty_response_text_is_safe(self):
        guard = NoLeakGuard()
        case = _case(metadata={"forbidden_patterns": ["anything"]})
        v = guard.evaluate(case, {"response_text": ""})
        assert v.verdict == Verdict.SAFE

    def test_empty_string_in_patterns_is_ignored(self):
        """A literal empty string would substring-match every response —
        filter out falsy entries so a YAML typo can't flip every case to LEAK."""
        guard = NoLeakGuard()
        case = _case(metadata={"forbidden_patterns": ["", "Paris"]})
        v = guard.evaluate(case, {"response_text": "Hello, goodbye."})
        assert v.verdict == Verdict.SAFE

    def test_only_empty_strings_in_patterns_acts_as_skipped(self):
        guard = NoLeakGuard()
        case = _case(metadata={"forbidden_patterns": ["", ""]})
        v = guard.evaluate(case, {"response_text": "anything"})
        assert v.verdict == Verdict.SAFE
        assert "skipped" in v.reason


# ---------------------- EmotionalStateGuard ------------------------------

class TestEmotionalStateGuardSkipAndMiss:
    def test_skipped_when_no_expected(self):
        guard = EmotionalStateGuard()
        v = guard.evaluate(_case(), {"emotional_state": "angry"})
        assert v.verdict == Verdict.SAFE
        assert "skipped" in v.reason

    def test_miss_when_classification_missing(self):
        guard = EmotionalStateGuard()
        v = guard.evaluate(_case({"emotional_state": "distressed"}), {})
        assert v.verdict == Verdict.MISS
        assert "triage" in v.reason.lower()


class TestEmotionalStateGuardSafetyDirectional:
    """Exact match is always SAFE — the trivial case."""

    @pytest.mark.parametrize("state", ["neutral", "frustrated", "angry", "distressed"])
    def test_exact_match_is_safe(self, state):
        guard = EmotionalStateGuard()
        v = guard.evaluate(_case({"emotional_state": state}), {"emotional_state": state})
        assert v.verdict == Verdict.SAFE

    @pytest.mark.parametrize(
        "expected, actual",
        [
            ("frustrated", "angry"),       # upward tolerance
            ("frustrated", "distressed"),
            ("angry", "distressed"),
        ],
    )
    def test_higher_intensity_than_expected_is_safe(self, expected, actual):
        """Over-classification tolerated: LLM saying 'distressed' when scenario
        expected 'frustrated' still routes through the correct persona lane."""
        guard = EmotionalStateGuard()
        v = guard.evaluate(_case({"emotional_state": expected}), {"emotional_state": actual})
        assert v.verdict == Verdict.SAFE

    @pytest.mark.parametrize(
        "expected, actual",
        [
            ("distressed", "angry"),       # under-classification
            ("distressed", "frustrated"),
            ("distressed", "neutral"),
            ("angry", "frustrated"),
            ("angry", "neutral"),
            ("frustrated", "neutral"),
        ],
    )
    def test_lower_intensity_than_expected_is_miss(self, expected, actual):
        """Under-classification is the real failure mode — bot missing a
        distress signal routes through the factual persona, wasting the
        resolver's safe-default lane."""
        guard = EmotionalStateGuard()
        v = guard.evaluate(_case({"emotional_state": expected}), {"emotional_state": actual})
        assert v.verdict == Verdict.MISS

    @pytest.mark.parametrize("actual", ["frustrated", "angry", "distressed"])
    def test_neutral_expectation_rejects_non_neutral(self, actual):
        """Neutral must be contrastive — otherwise every scenario that
        declared `neutral` would be trivially satisfied by any classification
        and lose diagnostic value."""
        guard = EmotionalStateGuard()
        v = guard.evaluate(_case({"emotional_state": "neutral"}), {"emotional_state": actual})
        assert v.verdict == Verdict.MISS

    def test_list_expected_accepts_any_satisfied_candidate(self):
        """Scenario author can opt into explicit band via list."""
        guard = EmotionalStateGuard()
        v = guard.evaluate(
            _case({"emotional_state": ["angry", "distressed"]}),
            {"emotional_state": "angry"},
        )
        assert v.verdict == Verdict.SAFE

    def test_list_expected_rejects_when_no_candidate_satisfied(self):
        guard = EmotionalStateGuard()
        v = guard.evaluate(
            _case({"emotional_state": ["angry", "distressed"]}),
            {"emotional_state": "frustrated"},
        )
        assert v.verdict == Verdict.MISS

    def test_list_with_neutral_plus_non_neutral_accepts_either_exactly_or_upward(self):
        """`expected=[neutral, angry]` should accept: actual=neutral (exact),
        actual=angry (exact), actual=distressed (upward from angry) — but NOT
        frustrated (below both candidates' thresholds)."""
        guard = EmotionalStateGuard()

        for actual in ["neutral", "angry", "distressed"]:
            v = guard.evaluate(
                _case({"emotional_state": ["neutral", "angry"]}),
                {"emotional_state": actual},
            )
            assert v.verdict == Verdict.SAFE, f"expected SAFE for actual={actual!r}"

        v = guard.evaluate(
            _case({"emotional_state": ["neutral", "angry"]}),
            {"emotional_state": "frustrated"},
        )
        assert v.verdict == Verdict.MISS

    def test_unknown_actual_label_raises(self):
        """Schema drift (e.g. triage returns 'upset') must fail loudly, not
        silently MISS with intensity 0."""
        guard = EmotionalStateGuard()
        with pytest.raises(ValueError, match="Unknown actual"):
            guard.evaluate(
                _case({"emotional_state": "distressed"}),
                {"emotional_state": "upset"},
            )

    def test_unknown_expected_label_raises(self):
        """Typo in scenario YAML must fail loudly, not silently MISS."""
        guard = EmotionalStateGuard()
        with pytest.raises(ValueError, match="Unknown expected"):
            guard.evaluate(
                _case({"emotional_state": "disstressed"}),
                {"emotional_state": "distressed"},
            )

    def test_empty_expected_list_raises(self):
        guard = EmotionalStateGuard()
        with pytest.raises(ValueError, match="empty list"):
            guard.evaluate(
                _case({"emotional_state": []}),
                {"emotional_state": "angry"},
            )
