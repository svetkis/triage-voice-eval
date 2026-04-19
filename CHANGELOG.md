# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `CasePersonaResult.error: str | None` field — populated when `pipeline_fn` raises,
  so a single failure no longer loses the rest of the run. Reports render error rows
  as `❌ ERROR` and count them as failures in the summary pass rate.

### Changed
- `EvalRunner.run` no longer mutates the dict returned by `pipeline_fn` — optional
  `_tokens` / `_cost` keys are read from a shallow copy.

### Removed (BREAKING)
- `Persona.prompt_files` and `Persona.model_config_override` — unused stubs
  never read by the runner. Wire such behavior into your own `pipeline_fn`
  via `persona.id`.

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
