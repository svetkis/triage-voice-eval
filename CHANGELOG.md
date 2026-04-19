# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `CasePersonaResult.error: str | None` field — populated when `pipeline_fn` raises,
  so a single failure no longer loses the rest of the run. Reports render error rows
  as `❌ ERROR` and count them as failures in the summary pass rate.
- Guards may now override `evaluate` as `async def`. The runner awaits
  coroutine returns transparently via `asyncio.iscoroutine`, which enables
  LLM-as-a-judge guards without blocking the event loop.
- `tve` CLI entrypoint with two subcommands: `tve trend <runs_dir>` prints
  the trend table, `tve report <result.json>` prints a summary. Pipelines
  still run through your own Python script.

### Changed
- `EvalRunner.run` no longer mutates the dict returned by `pipeline_fn` — optional
  `_tokens` / `_cost` keys are read from a shallow copy.
- `RunResult.timestamp` is now `datetime` (was `str`). Pydantic serializes
  it to ISO-8601 in JSON. Legacy files with `"timestamp": ""` are still
  accepted via a validator that maps them to `datetime.min` (UTC).
- `TrendAnalyzer.load_runs` now sorts by `result.timestamp` (with directory
  name as a deterministic tie-breaker), not by directory name alone.

### Deprecated
- `triage_voice_eval.usage_logger.UsageLogger` — use
  `triage_voice_eval.usage_tracker.UsageTracker` instead. The old name is
  a shim that emits `DeprecationWarning` and resolves to `UsageTracker`.
  The shim will be removed in v0.2. (Rename reflects the class's actual
  job: aggregation, not logging.)

### Removed (BREAKING)
- `Persona.prompt_files` and `Persona.model_config_override` — unused stubs
  never read by the runner. Wire such behavior into your own `pipeline_fn`
  via `persona.id`.
- `JailbreakGuard` no longer falls back to `str(response)` for pattern
  matching. Only fields listed in the new `text_fields` parameter
  (default `["response_text"]`) are scanned. Callers who relied on the
  old behavior should pass explicit `text_fields=[...]`.

## [0.1.0] - 2026-04-19

### Added
- Core abstractions: `Verdict`, `Guard`, `TestCase`, `Persona`, `Scenario`
- `CrisisGuard` — returns `SAFE` / `LEAK` / `MISS` verdicts for crisis detection
- `JailbreakGuard` — returns `HELD` / `BROKE` / `SAFE` verdicts for prompt injection
- `RobustJsonParser` — 5-stage JSON extraction with truncation repair
- `EvalRunner` — fan-out by persona with concurrency control
- `UsageLogger` — token/cost/latency tracking with percentiles
- `TrendAnalyzer` — regression detection and trend tables across runs
- `ReportGenerator` — case, persona, and matrix summary reports
- `examples/shopco_eval/` and `examples/multi_persona/` — runnable demonstrations
- README with comparison table (vs. DeepEval / promptfoo / RAGAS) and architecture guide

[Unreleased]: https://github.com/svetkis/triage-voice-eval/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/svetkis/triage-voice-eval/releases/tag/v0.1.0
