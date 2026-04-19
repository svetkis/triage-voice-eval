from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from .verdicts import VerdictResult


class TestCase(BaseModel):
    id: str
    input: str
    expected: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    history: list[dict[str, Any]] = Field(default_factory=list)


class Persona(BaseModel):
    id: str
    name: str


class CasePersonaResult(BaseModel):
    persona_id: str
    response: dict[str, Any] = Field(default_factory=dict)
    verdicts: list[VerdictResult] = Field(default_factory=list)
    latency_ms: float = 0.0
    tokens: dict[str, Any] = Field(default_factory=dict)
    cost: float = 0.0
    error: str | None = None


class RunResult(BaseModel):
    scenario_id: str
    results: dict[str, dict[str, CasePersonaResult]] = Field(default_factory=dict)
    timestamp: str = ""


class Scenario(BaseModel):
    id: str
    test_cases: list[TestCase]

    @classmethod
    def from_yaml(cls, path: str) -> Scenario:
        """Load scenario from YAML file.

        Raises:
            ValueError: if the file cannot be read or parsed.
        """
        p = Path(path)
        try:
            with open(p, encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except (FileNotFoundError, yaml.YAMLError) as exc:
            raise ValueError(f"Cannot load scenario from {path}: {exc}") from exc

        if isinstance(data, list):
            return cls(
                id=p.stem,
                test_cases=[TestCase(**item) for item in data],
            )

        return cls(
            id=data["id"],
            test_cases=[TestCase(**tc) for tc in data["test_cases"]],
        )
