# Security Policy

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

This project uses **GitHub Security Advisories** for private vulnerability disclosure:

1. Go to the [Security tab](../../security/advisories/new) of this repository.
2. Click **"Report a vulnerability"**.
3. Describe the issue, steps to reproduce, and impact.

You should receive an acknowledgment within **7 days**. If confirmed, we will coordinate a fix and a disclosure timeline with you before publishing any advisory.

## Scope

This project provides **binary safety guards** (CrisisGuard, JailbreakGuard) and evaluation infrastructure for safety-critical LLM pipelines. Security-relevant areas include:

- **Guard bypasses** — inputs that cause a guard to return `SAFE` when it should return `LEAK`, `MISS`, or `BROKE`
- **Verdict corruption** — defects in `RobustJsonParser` or guard logic that misclassify outcomes
- **Dependency vulnerabilities** in listed runtime dependencies (`pydantic`, `pyyaml`)

Test cases that expose a **novel** guard failure mode are a welcome security-adjacent contribution — please open an issue or PR rather than a security advisory unless the failure mode itself reveals a defect that could be exploited in downstream systems using this library as a gate.

## Supported Versions

Only the latest minor version on `main` receives security fixes while the project is pre-1.0.
