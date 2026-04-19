---
name: Feature request
about: Propose a new guard, report, or enhancement
title: "[feat] "
labels: enhancement
assignees: ''
---

## Problem / motivation

What safety property are you trying to evaluate that the current guards/reports don't cover? Concrete use case preferred over abstract wishes.

## Proposed change

What would you like to see added or changed?

## Alternatives considered

What other approaches did you think about, and why did you rule them out?

## Design fit — binary verdicts

This framework uses **binary verdicts**, not scores. If your proposal involves a new guard:

- What are the possible verdicts it returns? (e.g., `SAFE` / `LEAK`, or a new set)
- What input does it classify?
- Why is a verdict better than a continuous score for this property?

If your proposal is not about guards, skip this section.

## Additional context

Links, prior art, related issues.
