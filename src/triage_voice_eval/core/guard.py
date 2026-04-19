from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .models import TestCase
from .verdicts import VerdictResult


class Guard(ABC):
    """Base class for safety guards.

    Subclasses must set ``name`` (class attribute) and implement ``evaluate``.

    Contract:
    - ``evaluate`` must be **stateless** — it may be called concurrently
      from multiple asyncio tasks. Do not store mutable state between calls.
    - Document which ``case.expected`` keys your guard reads so users
      can catch typos early (e.g. ``is_crisis`` for CrisisGuard).
    """

    name: str

    @abstractmethod
    def evaluate(self, case: TestCase, response: dict[str, Any]) -> VerdictResult:
        """Evaluate a response against this guard's rules.

        Args:
            case: Test case with input and expected values.
            response: Raw dict returned by the pipeline function.

        Returns:
            VerdictResult with one of: SAFE, HELD, LEAK, MISS, BROKE.

        May be overridden as ``async def`` in subclasses that need I/O
        (e.g. LLM-as-a-judge). The runner awaits coroutine returns
        transparently.
        """
        ...
