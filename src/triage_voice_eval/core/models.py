from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel

from .verdicts import VerdictResult


class TestCase(BaseModel):
    id: str
    input: str
    expected: dict[str, Any] = {}
    metadata: dict[str, Any] = {}
    history: list[dict[str, Any]] = []


class Persona(BaseModel):
    id: str
    name: str
    prompt_files: list[str] = []
    model_config_override: dict[str, Any] = {}


class CasePersonaResult(BaseModel):
    persona_id: str
    response: dict[str, Any] = {}
    verdicts: list[VerdictResult] = []
    latency_ms: float = 0.0
    tokens: dict[str, Any] = {}
    cost: float = 0.0


class RunResult(BaseModel):
    scenario_id: str
    results: dict[str, dict[str, CasePersonaResult]] = {}
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
            with open(p) as f:
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
