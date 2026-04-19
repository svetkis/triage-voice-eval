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
        """Run all test cases × personas through pipeline_fn and evaluate with guards."""
        semaphore = asyncio.Semaphore(concurrency)
        results: dict[str, dict[str, CasePersonaResult]] = {}

        async def _run_one(case: TestCase, persona: Persona) -> tuple[str, str, CasePersonaResult]:
            async with semaphore:
                t0 = time.perf_counter()
                response = await pipeline_fn(case, persona)
                latency_ms = (time.perf_counter() - t0) * 1000

            verdicts = [guard.evaluate(case, response) for guard in guards]

            cpr = CasePersonaResult(
                persona_id=persona.id,
                response=response,
                verdicts=verdicts,
                latency_ms=latency_ms,
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
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
