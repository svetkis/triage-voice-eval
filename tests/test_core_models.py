import pytest
import yaml
from pathlib import Path

from triage_voice_eval.core import (
    Verdict,
    VerdictResult,
    Guard,
    TestCase,
    Persona,
    Scenario,
    CasePersonaResult,
    RunResult,
)


class TestTestCase:
    def test_defaults(self):
        tc = TestCase(id="t1", input="hello")
        assert tc.id == "t1"
        assert tc.input == "hello"
        assert tc.expected == {}
        assert tc.metadata == {}
        assert tc.history == []

    def test_full_data(self):
        tc = TestCase(
            id="t2",
            input="are you real?",
            expected={"is_crisis": True},
            metadata={"source": "manual"},
            history=[{"role": "user", "content": "hi"}],
        )
        assert tc.expected == {"is_crisis": True}
        assert tc.metadata["source"] == "manual"
        assert len(tc.history) == 1


class TestVerdict:
    def test_enum_values(self):
        assert Verdict.SAFE == "safe"
        assert Verdict.LEAK == "leak"
        assert Verdict.MISS == "miss"
        assert Verdict.HELD == "held"
        assert Verdict.BROKE == "broke"

    def test_all_members(self):
        names = {v.value for v in Verdict}
        assert names == {"safe", "leak", "miss", "held", "broke"}


class TestVerdictResult:
    def test_creation(self):
        vr = VerdictResult(
            verdict=Verdict.LEAK,
            guard_name="secret_guard",
            reason="leaked API key",
            evidence="sk-abc123",
        )
        assert vr.verdict == Verdict.LEAK
        assert vr.guard_name == "secret_guard"
        assert vr.reason == "leaked API key"
        assert vr.evidence == "sk-abc123"

    def test_evidence_default(self):
        vr = VerdictResult(
            verdict=Verdict.SAFE,
            guard_name="g1",
            reason="all good",
        )
        assert vr.evidence == ""


class TestScenarioFromYaml:
    def test_list_format(self, tmp_path: Path):
        data = [
            {"id": "c1", "input": "hello"},
            {"id": "c2", "input": "bye", "expected": {"tone": "polite"}},
        ]
        f = tmp_path / "greetings.yaml"
        f.write_text(yaml.dump(data))

        scenario = Scenario.from_yaml(str(f))
        assert scenario.id == "greetings"
        assert len(scenario.test_cases) == 2
        assert scenario.test_cases[0].id == "c1"
        assert scenario.test_cases[1].expected == {"tone": "polite"}

    def test_cyrillic_utf8(self, tmp_path: Path):
        """UTF-8 YAML with cyrillic chars loads regardless of platform locale."""
        data = {
            "id": "кризис",
            "test_cases": [
                {"id": "c1", "input": "мне плохо", "expected": {"is_crisis": True}},
            ],
        }
        f = tmp_path / "ru.yaml"
        f.write_bytes(yaml.dump(data, allow_unicode=True).encode("utf-8"))

        scenario = Scenario.from_yaml(str(f))
        assert scenario.id == "кризис"
        assert scenario.test_cases[0].input == "мне плохо"

    def test_dict_format(self, tmp_path: Path):
        data = {
            "id": "crisis",
            "test_cases": [
                {"id": "c1", "input": "I want to end it all"},
            ],
        }
        f = tmp_path / "crisis.yaml"
        f.write_text(yaml.dump(data))

        scenario = Scenario.from_yaml(str(f))
        assert scenario.id == "crisis"
        assert len(scenario.test_cases) == 1


class TestCasePersonaResult:
    def test_defaults(self):
        r = CasePersonaResult(persona_id="nastya")
        assert r.persona_id == "nastya"
        assert r.response == {}
        assert r.verdicts == []
        assert r.latency_ms == 0.0
        assert r.tokens == {}
        assert r.cost == 0.0
        assert r.error is None


class TestRunResult:
    def test_defaults(self):
        r = RunResult(scenario_id="s1")
        assert r.results == {}
        assert r.timestamp == ""


class TestPersona:
    def test_creation(self):
        p = Persona(id="nastya", name="Nastya")
        assert p.id == "nastya"
        assert p.name == "Nastya"
