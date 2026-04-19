from enum import Enum

from pydantic import BaseModel


class Verdict(str, Enum):
    SAFE = "safe"
    LEAK = "leak"
    MISS = "miss"
    HELD = "held"
    BROKE = "broke"


class VerdictResult(BaseModel):
    verdict: Verdict
    guard_name: str
    reason: str
    evidence: str = ""
