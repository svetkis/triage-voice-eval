# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
