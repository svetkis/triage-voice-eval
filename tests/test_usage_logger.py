import pytest

from triage_voice_eval.usage_logger import UsageLogger


def test_log_and_summary():
    logger = UsageLogger(cost_per_1m_input=3.0, cost_per_1m_output=15.0)
    logger.log(1000, 200, 150.0)
    logger.log(800, 300, 250.0)
    s = logger.summary()
    assert s.total_calls == 2
    assert s.total_input_tokens == 1800
    assert s.total_output_tokens == 500


def test_cost_calculation():
    logger = UsageLogger(cost_per_1m_input=3.0, cost_per_1m_output=15.0)
    logger.log(1_000_000, 0, 100.0)  # exactly 1M input tokens
    s = logger.summary()
    assert s.total_cost == pytest.approx(3.0)


def test_cost_calculation_output():
    logger = UsageLogger(cost_per_1m_input=3.0, cost_per_1m_output=15.0)
    logger.log(0, 1_000_000, 100.0)  # exactly 1M output tokens
    s = logger.summary()
    assert s.total_cost == pytest.approx(15.0)


def test_cost_calculation_mixed():
    logger = UsageLogger(cost_per_1m_input=3.0, cost_per_1m_output=15.0)
    logger.log(1000, 200, 100.0)
    s = logger.summary()
    # 1000 / 1_000_000 * 3.0 = 0.003
    # 200 / 1_000_000 * 15.0 = 0.003
    assert s.total_cost == pytest.approx(0.006)


def test_percentiles():
    logger = UsageLogger()
    for i in range(100):
        logger.log(100, 50, float(i + 1))  # latencies 1..100
    s = logger.summary()
    assert s.latency_p50 == pytest.approx(50.0, abs=1)
    assert s.latency_p95 == pytest.approx(95.0, abs=1)
    assert s.latency_p99 == pytest.approx(99.0, abs=1)


def test_empty_logger():
    logger = UsageLogger()
    s = logger.summary()
    assert s.total_calls == 0
    assert s.total_input_tokens == 0
    assert s.total_output_tokens == 0
    assert s.total_cost == 0.0
    assert s.latency_p50 == 0.0
    assert s.latency_p95 == 0.0
    assert s.latency_p99 == 0.0
    assert s.avg_latency == 0.0


def test_to_markdown():
    logger = UsageLogger()
    logger.log(100, 50, 200.0)
    md = logger.to_markdown()
    assert "Total calls" in md
    assert "1" in md  # total calls
    assert "Usage Summary" in md
    assert "| Metric | Value |" in md


def test_to_dict():
    logger = UsageLogger(cost_per_1m_input=3.0, cost_per_1m_output=15.0)
    logger.log(1000, 200, 150.0)
    d = logger.to_dict()
    assert d["total_calls"] == 1
    assert d["total_input_tokens"] == 1000
    assert d["total_output_tokens"] == 200
    assert "latency_p50" in d
    assert "total_cost" in d


def test_single_record_percentiles():
    logger = UsageLogger()
    logger.log(100, 50, 42.0)
    s = logger.summary()
    assert s.latency_p50 == 42.0
    assert s.latency_p95 == 42.0
    assert s.latency_p99 == 42.0
    assert s.avg_latency == 42.0
