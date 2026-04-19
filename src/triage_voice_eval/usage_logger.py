"""Deprecated shim: UsageLogger was renamed to UsageTracker.

Kept for one minor version to preserve backward compatibility. Import from
:mod:`triage_voice_eval.usage_tracker` instead.
"""

from __future__ import annotations

import warnings

from .usage_tracker import UsageRecord, UsageSummary, UsageTracker

__all__ = ["UsageLogger", "UsageRecord", "UsageSummary", "UsageTracker"]


def __getattr__(name: str):
    if name == "UsageLogger":
        warnings.warn(
            "UsageLogger has been renamed to UsageTracker; import from "
            "triage_voice_eval.usage_tracker. The old name will be removed "
            "in v0.2.",
            DeprecationWarning,
            stacklevel=2,
        )
        return UsageTracker
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
