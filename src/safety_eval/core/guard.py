from __future__ import annotations

from abc import ABC, abstractmethod

from .models import TestCase
from .verdicts import VerdictResult


class Guard(ABC):
    name: str

    @abstractmethod
    def evaluate(self, case: TestCase, response: dict) -> VerdictResult:
        """Evaluate a response against this guard's rules."""
        ...
