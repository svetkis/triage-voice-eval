---
name: Bug report
about: Report a defect in a guard, parser, runner, or report generator
title: "[bug] "
labels: bug
assignees: ''
---

## Summary

A clear one-sentence description of the bug.

## Affected component

- [ ] CrisisGuard / JailbreakGuard (verdict logic)
- [ ] RobustJsonParser
- [ ] EvalRunner (fan-out / concurrency)
- [ ] UsageLogger / ReportGenerator / TrendAnalyzer
- [ ] Other — explain:

## Reproduction

Minimal steps to reproduce:

1. ...
2. ...
3. ...

**Input** (test case / model output / JSON):
```
...
```

**Expected verdict / behavior**:

**Actual verdict / behavior**:

## Environment

- Python version: `python --version`
- Package version / commit: `pip show triage-voice-eval` or `git rev-parse HEAD`
- OS:
- LLM provider / model used in the test (if applicable):

## Logs / traceback

```
<paste relevant logs here — redact any API keys or PII>
```

## Additional context

Anything else that might help — screenshots, related issues, hypotheses.
