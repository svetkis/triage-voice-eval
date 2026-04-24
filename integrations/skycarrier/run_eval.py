"""SkyCarrier eval entry point.

Usage:
    python -m integrations.skycarrier.run_eval [--save-json RESULT_PATH]

Requires:
    - OPENAI_API_KEY (triage-and-voice pipeline calls the OpenAI API)
    - c:/Repos/triage-and-voice checked out as a sibling directory,
      with dependencies installed.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
from pathlib import Path

from triage_voice_eval import (
    EvalRunner,
    Persona,
    Scenario,
    generate_persona_report,
    generate_summary,
)

from integrations.skycarrier.guards import (
    EmotionalStateGuard,
    HandoffGuard,
    IntentGuard,
    NoLeakGuard,
)
from integrations.skycarrier.pipeline import run_pipeline

_SCENARIOS_PATH = Path(__file__).parent / "scenarios.yaml"


async def main(save_path: Path | None) -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    scenario = Scenario.from_yaml(str(_SCENARIOS_PATH))

    # Single persona — the SkyCarrier vertical is configured with multiple
    # voice personas internally (bereavement_support, factual_fare_terms, ...)
    # but those are selected by the gate, not by this outer persona loop.
    # If a future change wants persona-level fan-out (e.g. run the same
    # scenarios against a baseline naive_skycarrier_bot), add it here.
    personas = [Persona(id="triage_voice", name="SkyCarrier triage+voice")]

    guards = [
        IntentGuard(),
        EmotionalStateGuard(),
        HandoffGuard(),
        NoLeakGuard(),
    ]

    runner = EvalRunner()
    result = await runner.run(scenario, personas, guards, run_pipeline, concurrency=3)

    print(generate_summary(result))
    print()
    print(generate_persona_report("triage_voice", result))

    if save_path is not None:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        save_path.write_text(result.model_dump_json(indent=2), encoding="utf-8")
        print(f"\nSaved result to {save_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--save-json",
        type=Path,
        default=None,
        help="Write RunResult JSON to this path (for trend analysis).",
    )
    args = parser.parse_args()

    asyncio.run(main(args.save_json))
