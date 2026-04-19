"""Usage logger for tracking tokens, cost, and latency across eval runs."""

from __future__ import annotations

import math

from pydantic import BaseModel


class UsageRecord(BaseModel):
    input_tokens: int
    output_tokens: int
    latency_ms: float
    cost: float


class UsageSummary(BaseModel):
    total_calls: int
    total_input_tokens: int
    total_output_tokens: int
    total_cost: float
    latency_p50: float
    latency_p95: float
    latency_p99: float
    avg_latency: float


class UsageLogger:
    """Track token usage, cost, and latency across eval calls.

    Thread safety: this class is safe for use within a single asyncio
    event loop but is NOT thread-safe. Do not share an instance across
    threads without external synchronization.
    """

    def __init__(
        self,
        cost_per_1m_input: float = 0.0,
        cost_per_1m_output: float = 0.0,
    ):
        self._cost_per_1m_input = cost_per_1m_input
        self._cost_per_1m_output = cost_per_1m_output
        self._records: list[UsageRecord] = []

    def log(self, input_tokens: int, output_tokens: int, latency_ms: float) -> None:
        """Record a single LLM call."""
        cost = (
            input_tokens / 1_000_000 * self._cost_per_1m_input
            + output_tokens / 1_000_000 * self._cost_per_1m_output
        )
        self._records.append(
            UsageRecord(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                cost=cost,
            )
        )

    def summary(self) -> UsageSummary:
        """Compute aggregate statistics."""
        if not self._records:
            return UsageSummary(
                total_calls=0,
                total_input_tokens=0,
                total_output_tokens=0,
                total_cost=0.0,
                latency_p50=0.0,
                latency_p95=0.0,
                latency_p99=0.0,
                avg_latency=0.0,
            )

        latencies = sorted(r.latency_ms for r in self._records)

        return UsageSummary(
            total_calls=len(self._records),
            total_input_tokens=sum(r.input_tokens for r in self._records),
            total_output_tokens=sum(r.output_tokens for r in self._records),
            total_cost=sum(r.cost for r in self._records),
            latency_p50=self._percentile(latencies, 0.50),
            latency_p95=self._percentile(latencies, 0.95),
            latency_p99=self._percentile(latencies, 0.99),
            avg_latency=sum(latencies) / len(latencies),
        )

    def to_markdown(self) -> str:
        """Format summary as markdown table."""
        s = self.summary()
        return (
            "## Usage Summary\n"
            "\n"
            "| Metric | Value |\n"
            "|--------|-------|\n"
            f"| Total calls | {s.total_calls:,} |\n"
            f"| Total input tokens | {s.total_input_tokens:,} |\n"
            f"| Total output tokens | {s.total_output_tokens:,} |\n"
            f"| Total cost | ${s.total_cost:.2f} |\n"
            f"| Avg latency | {s.avg_latency:.0f}ms |\n"
            f"| P50 latency | {s.latency_p50:.0f}ms |\n"
            f"| P95 latency | {s.latency_p95:.0f}ms |\n"
            f"| P99 latency | {s.latency_p99:.0f}ms |\n"
        )

    def to_dict(self) -> dict:
        """Format summary as dict (for JSON serialization)."""
        return self.summary().model_dump()

    @staticmethod
    def _percentile(sorted_values: list[float], p: float) -> float:
        """Pick value at percentile position. index = ceil(n * p) - 1."""
        n = len(sorted_values)
        if n == 0:
            return 0.0
        idx = math.ceil(n * p) - 1
        idx = max(0, min(idx, n - 1))
        return sorted_values[idx]
