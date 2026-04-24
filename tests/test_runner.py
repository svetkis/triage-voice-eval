from __future__ import annotations

import asyncio
import logging

import pytest

from triage_voice_eval.core import (
    CasePersonaResult,
    Guard,
    Persona,
    Scenario,
    TestCase,
    Verdict,
    VerdictResult,
)
from triage_voice_eval.runner import EvalRunner


@pytest.fixture
def two_cases_two_personas():
    scenario = Scenario(
        id="s1",
        test_cases=[
            TestCase(id="c1", input="hello"),
            TestCase(id="c2", input="bye"),
        ],
    )
    personas = [
        Persona(id="p1", name="P1"),
        Persona(id="p2", name="P2"),
    ]
    return scenario, personas


@pytest.mark.asyncio
async def test_runner_fan_out(two_cases_two_personas):
    """2 cases × 2 personas = 4 pipeline calls."""
    scenario, personas = two_cases_two_personas
    calls: list[tuple[str, str]] = []

    async def mock_pipeline(case: TestCase, persona: Persona) -> dict:
        calls.append((case.id, persona.id))
        return {"text": f"response for {case.id} by {persona.id}"}

    runner = EvalRunner()
    result = await runner.run(scenario, personas, [], mock_pipeline)

    assert len(calls) == 4
    assert "c1" in result.results
    assert "c2" in result.results
    assert "p1" in result.results["c1"]
    assert "p2" in result.results["c1"]
    assert result.scenario_id == "s1"
    assert result.timestamp != ""


@pytest.mark.asyncio
async def test_runner_applies_guards(two_cases_two_personas):
    """Guards evaluate each response."""
    scenario, personas = two_cases_two_personas

    class AlwaysSafeGuard(Guard):
        name = "always_safe"

        def evaluate(self, case: TestCase, response: dict) -> VerdictResult:
            return VerdictResult(
                verdict=Verdict.SAFE,
                guard_name=self.name,
                reason="all good",
            )

    async def mock_pipeline(case: TestCase, persona: Persona) -> dict:
        return {"text": "ok"}

    runner = EvalRunner()
    result = await runner.run(scenario, personas, [AlwaysSafeGuard()], mock_pipeline)

    for case_id in result.results:
        for persona_id in result.results[case_id]:
            cpr = result.results[case_id][persona_id]
            assert len(cpr.verdicts) == 1
            assert cpr.verdicts[0].verdict == Verdict.SAFE
            assert cpr.verdicts[0].guard_name == "always_safe"


@pytest.mark.asyncio
async def test_runner_measures_latency():
    """Latency is recorded for each call."""
    scenario = Scenario(id="s1", test_cases=[TestCase(id="c1", input="hi")])
    personas = [Persona(id="p1", name="P1")]

    async def slow_pipeline(case: TestCase, persona: Persona) -> dict:
        await asyncio.sleep(0.05)
        return {"text": "slow"}

    runner = EvalRunner()
    result = await runner.run(scenario, personas, [], slow_pipeline)

    cpr = result.results["c1"]["p1"]
    assert cpr.latency_ms >= 40  # at least ~50ms minus jitter


@pytest.mark.asyncio
async def test_runner_awaits_async_guard():
    """A guard with async def evaluate is awaited by the runner."""

    class AsyncGuard(Guard):
        name = "async_g"

        async def evaluate(self, case: TestCase, response: dict) -> VerdictResult:
            await asyncio.sleep(0)  # yield to event loop
            return VerdictResult(
                verdict=Verdict.SAFE, guard_name=self.name, reason="async ok"
            )

    scenario = Scenario(id="s1", test_cases=[TestCase(id="c1", input="hi")])
    personas = [Persona(id="p1", name="P1")]

    async def pipeline(case: TestCase, persona: Persona) -> dict:
        return {"text": "ok"}

    runner = EvalRunner()
    result = await runner.run(scenario, personas, [AsyncGuard()], pipeline)

    cpr = result.results["c1"]["p1"]
    assert cpr.error is None
    assert len(cpr.verdicts) == 1
    assert cpr.verdicts[0].verdict == Verdict.SAFE
    assert cpr.verdicts[0].reason == "async ok"


@pytest.mark.asyncio
async def test_runner_isolates_pipeline_failure(two_cases_two_personas):
    """One pipeline_fn raising doesn't lose the other results."""
    scenario, personas = two_cases_two_personas

    async def flaky_pipeline(case: TestCase, persona: Persona) -> dict:
        if case.id == "c1" and persona.id == "p1":
            raise RuntimeError("boom")
        return {"text": "ok"}

    runner = EvalRunner()
    result = await runner.run(scenario, personas, [], flaky_pipeline)

    failed = result.results["c1"]["p1"]
    assert failed.error is not None
    assert "RuntimeError" in failed.error
    assert "boom" in failed.error
    assert failed.verdicts == []
    assert failed.response == {}

    for case_id, persona_id in [("c1", "p2"), ("c2", "p1"), ("c2", "p2")]:
        ok = result.results[case_id][persona_id]
        assert ok.error is None
        assert ok.response == {"text": "ok"}


@pytest.mark.asyncio
async def test_runner_does_not_mutate_pipeline_response():
    """pipeline_fn's returned dict (including _tokens/_cost/_latency_ms) is not mutated."""
    scenario = Scenario(id="s1", test_cases=[TestCase(id="c1", input="hi")])
    personas = [Persona(id="p1", name="P1")]

    shared = {
        "text": "ok",
        "_tokens": {"in": 10, "out": 20},
        "_cost": 0.01,
        "_latency_ms": 42.0,
    }

    async def pipeline(case: TestCase, persona: Persona) -> dict:
        return shared

    runner = EvalRunner()
    result = await runner.run(scenario, personas, [], pipeline)

    assert "_tokens" in shared and shared["_tokens"] == {"in": 10, "out": 20}
    assert "_cost" in shared and shared["_cost"] == 0.01
    assert "_latency_ms" in shared and shared["_latency_ms"] == 42.0

    cpr = result.results["c1"]["p1"]
    assert cpr.tokens == {"in": 10, "out": 20}
    assert cpr.cost == 0.01
    assert "_tokens" not in cpr.response
    assert "_cost" not in cpr.response
    assert "_latency_ms" not in cpr.response


@pytest.mark.asyncio
async def test_runner_strips_latency_ms_from_response():
    """_latency_ms leaked from pipeline_fn is stripped from stored response."""
    scenario = Scenario(id="s1", test_cases=[TestCase(id="c1", input="hi")])
    personas = [Persona(id="p1", name="P1")]

    async def pipeline(case: TestCase, persona: Persona) -> dict:
        return {"response_text": "ok", "_latency_ms": 123.45}

    runner = EvalRunner()
    result = await runner.run(scenario, personas, [], pipeline)

    cpr = result.results["c1"]["p1"]
    assert "_latency_ms" not in cpr.response
    assert cpr.response == {"response_text": "ok"}


@pytest.mark.asyncio
async def test_runner_logs_pipeline_exception(caplog):
    """A raising pipeline_fn produces an ERROR-level log record identifying the pair."""
    caplog.set_level(logging.ERROR, logger="triage_voice_eval.runner")

    scenario = Scenario(id="s1", test_cases=[TestCase(id="c1", input="hi")])
    personas = [Persona(id="p1", name="P1")]

    async def boom_pipeline(case: TestCase, persona: Persona) -> dict:
        raise ValueError("boom")

    runner = EvalRunner()
    result = await runner.run(scenario, personas, [], boom_pipeline)

    # Result still contains the error
    assert "ValueError" in result.results["c1"]["p1"].error

    error_records = [
        r for r in caplog.records
        if r.levelno == logging.ERROR and r.name == "triage_voice_eval.runner"
    ]
    assert error_records, "expected an ERROR record on pipeline_fn failure"
    msg = error_records[0].getMessage()
    assert "c1" in msg
    assert "p1" in msg


@pytest.mark.asyncio
async def test_runner_respects_concurrency():
    """Concurrency limit is respected."""
    max_concurrent = 0
    current = 0
    lock = asyncio.Lock()

    async def tracking_pipeline(case: TestCase, persona: Persona) -> dict:
        nonlocal max_concurrent, current
        async with lock:
            current += 1
            max_concurrent = max(max_concurrent, current)
        await asyncio.sleep(0.05)
        async with lock:
            current -= 1
        return {}

    scenario = Scenario(
        id="s1",
        test_cases=[TestCase(id=f"c{i}", input=f"msg{i}") for i in range(6)],
    )
    personas = [Persona(id="p1", name="P1"), Persona(id="p2", name="P2")]

    runner = EvalRunner()
    await runner.run(scenario, personas, [], tracking_pipeline, concurrency=2)

    assert max_concurrent <= 2
