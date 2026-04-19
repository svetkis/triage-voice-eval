# Contributing

Thanks for your interest in contributing. This project is an **evaluation framework** for safety-critical LLM pipelines — scope is deliberately narrow and opinionated.

## Before you start

- Open an **issue first** for any non-trivial change. A PR without a preceding issue is likely to be closed, because scope discussions happen on issues, not in review.
- Read [README.md](README.md) — especially the "When to use this (and when not to)" section — to understand what problem this framework solves and what it deliberately does not.

## Development setup

Requires **Python 3.11+**.

```bash
git clone <your-fork-url>
cd triage-voice-eval
make install           # pip install -e ".[dev,examples]"
cp .env.example .env   # add your OPENAI_API_KEY (only needed for examples)
make test              # pytest -v
make example-shopco    # run the ShopCo eval
make example-multi-persona
```

## What kinds of contributions are welcome

- **New guard implementations** that return **binary verdicts** (not scores) for a well-defined safety property
- **Bug fixes** with a failing test that demonstrates the bug
- **New test cases / personas** in `examples/` that exercise guard edge cases
- **Parser robustness** — adversarial JSON inputs that `RobustJsonParser` currently mis-handles
- **Doc improvements** — clarity, typos, missing setup steps

## Scope — what I may decline

This section will grow as patterns emerge in real PRs. The guiding principle:

> **Binary verdicts are a core design constraint, not a limitation to be fixed.**

Proposals that blur the `SAFE` / `HELD` / `LEAK` / `MISS` / `BROKE` model — for example, adding continuous "safety scores" or fuzzy classifiers — will be scrutinized heavily. The framework exists because "0.73 safety score" is not useful for safety-critical systems; a verdict is.

If you're unsure whether your idea fits, open an issue and ask before investing time.

## Pull request checklist

- [ ] Linked to an existing issue (or explained why one isn't needed)
- [ ] Tests pass: `make test`
- [ ] New code has test coverage
- [ ] `CHANGELOG.md` updated under `[Unreleased]`
- [ ] Commit messages follow the existing style (see `git log`)

## Commit style

Conventional-ish, lowercase type prefix:

```
feat: add new guard for PII leakage detection
fix: handle nested JSON objects in RobustJsonParser stage 4
docs: clarify verdict semantics in README
```

## Reporting security issues

Do **not** open a public issue for security vulnerabilities. See [SECURITY.md](SECURITY.md).
