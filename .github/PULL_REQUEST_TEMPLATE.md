## Summary

<!-- 1–3 sentences: what changes and why. -->

## Related issue

Closes #

<!-- Non-trivial PRs without a linked issue are likely to be closed. Open an issue first to align on scope. -->

## Type of change

- [ ] Bug fix
- [ ] New guard (binary verdicts)
- [ ] New test case / persona / example
- [ ] Parser robustness improvement
- [ ] Documentation
- [ ] Other — explain:

## Design fit

If this PR adds a new guard or changes verdict semantics, confirm:

- [ ] Guard returns a **verdict**, not a score
- [ ] All possible verdicts are documented
- [ ] Failure modes (`LEAK` / `MISS` / `BROKE`) are distinguished from non-applicable (`SAFE`)

## Test plan

- [ ] `make test` passes
- [ ] New/changed behavior has test coverage
- [ ] Adversarial input added to tests (if guard or parser change)
- [ ] Example eval run verified (if runner/report change)

## Checklist

- [ ] `CHANGELOG.md` updated under `[Unreleased]`
- [ ] No secrets, API keys, or PII in the diff
- [ ] Commit messages follow project style
