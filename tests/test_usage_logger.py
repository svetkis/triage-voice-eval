"""Deprecation shim tests for UsageLogger — removes in v0.2."""

import warnings

from triage_voice_eval.usage_tracker import UsageTracker


def test_old_import_path_still_works_with_deprecation_warning():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        from triage_voice_eval.usage_logger import UsageLogger

        assert UsageLogger is UsageTracker

    deprecations = [w for w in caught if issubclass(w.category, DeprecationWarning)]
    assert deprecations, "expected a DeprecationWarning from UsageLogger import"
    assert "UsageTracker" in str(deprecations[0].message)


def test_old_import_path_instance_is_usage_tracker():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        from triage_voice_eval.usage_logger import UsageLogger

    instance = UsageLogger(cost_per_1m_input=1.0, cost_per_1m_output=2.0)
    assert isinstance(instance, UsageTracker)
