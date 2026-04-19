from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone

from .core import (
    CasePersonaResult,
    Guard,
    Persona,
    RunResult,
    Scenario,
    TestCase,
)


class EvalRunner:
    """Orchestrates test-case × persona fan-out with guard evaluation."""

    async def run(
        self,
        scenario: Scenario,
        personas: list[Persona],
        guards: list[Guard],
        pipeline_fn: Callable[[TestCase, Persona], Awaitable[dict]],
        concurrency: int = 3,
    ) -> RunResult:
        """Run all test cases × personas through pipeline_fn and evaluate with guards.

        If ``pipeline_fn`` raises for a given (case, persona), the failure is
        recorded on that ``CasePersonaResult.error`` and other pairs still run.

        The dict returned by ``pipeline_fn`` is not mutated — optional
        ``_tokens``/``_cost`` keys are read from a shallow copy.
        """
        semaphore = asyncio.Semaphore(concurrency)
        results: dict[str, dict[str, CasePersonaResult]] = {}

        async def _run_one(case: TestCase, persona: Persona) -> tuple[str, str, CasePersonaResult]:
            async with semaphore:
                t0 = time.perf_counter()
                try:
                    raw_response = await pipeline_fn(case, persona)
                except Exception as exc:
                    latency_ms = (time.perf_counter() - t0) * 1000
                    cpr = CasePersonaResult(
                        persona_id=persona.id,
                        response={},
                        verdicts=[],
                        latency_ms=latency_ms,
                        error=f"{type(exc).__name__}: {exc}",
                    )
                    return case.id, persona.id, cpr
                latency_ms = (time.perf_counter() - t0) * 1000

            # Shallow copy so we don't mutate the caller's dict when
            # extracting optional _tokens / _cost usage metadata.
            response = dict(raw_response)
            tokens = response.pop("_tokens", {})
            cost = response.pop("_cost", 0.0)

            verdicts = [guard.evaluate(case, response) for guard in guards]

            cpr = CasePersonaResult(
                persona_id=persona.id,
                response=response,
                verdicts=verdicts,
                latency_ms=latency_ms,
                tokens=tokens,
                cost=cost,
            )
            return case.id, persona.id, cpr

        tasks = [
            _run_one(case, persona)
            for case in scenario.test_cases
            for persona in personas
        ]
        completed = await asyncio.gather(*tasks)

        for case_id, persona_id, cpr in completed:
            results.setdefault(case_id, {})[persona_id] = cpr

        return RunResult(
            scenario_id=scenario.id,
            results=results,
            timestamp=datetime.now(timezone.utc),
        )
