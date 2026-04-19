import pytest

from triage_voice_eval.usage_tracker import UsageTracker


def test_log_and_summary():
    tracker = UsageTracker(cost_per_1m_input=3.0, cost_per_1m_output=15.0)
    tracker.log(1000, 200, 150.0)
    tracker.log(800, 300, 250.0)
    s = tracker.summary()
    assert s.total_calls == 2
    assert s.total_input_tokens == 1800
    assert s.total_output_tokens == 500


def test_cost_calculation():
    tracker = UsageTracker(cost_per_1m_input=3.0, cost_per_1m_output=15.0)
    tracker.log(1_000_000, 0, 100.0)
    s = tracker.summary()
    assert s.total_cost == pytest.approx(3.0)


def test_cost_calculation_output():
    tracker = UsageTracker(cost_per_1m_input=3.0, cost_per_1m_output=15.0)
    tracker.log(0, 1_000_000, 100.0)
    s = tracker.summary()
    assert s.total_cost == pytest.approx(15.0)


def test_cost_calculation_mixed():
    tracker = UsageTracker(cost_per_1m_input=3.0, cost_per_1m_output=15.0)
    tracker.log(1000, 200, 100.0)
    s = tracker.summary()
    assert s.total_cost == pytest.approx(0.006)


def test_percentiles():
    tracker = UsageTracker()
    for i in range(100):
        tracker.log(100, 50, float(i + 1))
    s = tracker.summary()
    assert s.latency_p50 == pytest.approx(50.0, abs=1)
    assert s.latency_p95 == pytest.approx(95.0, abs=1)
    assert s.latency_p99 == pytest.approx(99.0, abs=1)


def test_empty_tracker():
    tracker = UsageTracker()
    s = tracker.summary()
    assert s.total_calls == 0
    assert s.total_input_tokens == 0
    assert s.total_output_tokens == 0
    assert s.total_cost == 0.0
    assert s.latency_p50 == 0.0
    assert s.latency_p95 == 0.0
    assert s.latency_p99 == 0.0
    assert s.avg_latency == 0.0


def test_to_markdown():
    tracker = UsageTracker()
    tracker.log(100, 50, 200.0)
    md = tracker.to_markdown()
    assert "Total calls" in md
    assert "Usage Summary" in md
    assert "| Metric | Value |" in md


def test_to_dict():
    tracker = UsageTracker(cost_per_1m_input=3.0, cost_per_1m_output=15.0)
    tracker.log(1000, 200, 150.0)
    d = tracker.to_dict()
    assert d["total_calls"] == 1
    assert d["total_input_tokens"] == 1000
    assert d["total_output_tokens"] == 200
    assert "latency_p50" in d
    assert "total_cost" in d


def test_single_record_percentiles():
    tracker = UsageTracker()
    tracker.log(100, 50, 42.0)
    s = tracker.summary()
    assert s.latency_p50 == 42.0
    assert s.latency_p95 == 42.0
    assert s.latency_p99 == 42.0
    assert s.avg_latency == 42.0
