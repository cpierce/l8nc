"""Tests for the data models."""

from __future__ import annotations

from l8nc.models import PingResult, TargetStats


def test_ping_result_success():
    r = PingResult(timestamp=1000.0, latency_ms=15.5)
    assert r.is_success is True


def test_ping_result_timeout():
    r = PingResult(timestamp=1000.0, latency_ms=None)
    assert r.is_success is False


def test_target_stats_empty():
    t = TargetStats(address="1.2.3.4", label="test")
    assert t.min_ms is None
    assert t.avg_ms is None
    assert t.max_ms is None
    assert t.loss_pct == 0.0
    assert t.latest_ms is None
    assert t.successful_latencies == []


def test_target_stats_record():
    t = TargetStats(address="1.2.3.4", label="test")
    t.record(10.0)
    t.record(20.0)
    t.record(30.0)
    assert t.min_ms == 10.0
    assert t.max_ms == 30.0
    assert t.avg_ms == 20.0
    assert t.loss_pct == 0.0
    assert t.latest_ms == 30.0
    assert len(t.history) == 3


def test_target_stats_with_timeouts():
    t = TargetStats(address="1.2.3.4", label="test")
    t.record(10.0)
    t.record(None)
    t.record(20.0)
    t.record(None)
    assert t.min_ms == 10.0
    assert t.max_ms == 20.0
    assert t.avg_ms == 15.0
    assert t.loss_pct == 50.0
    assert t.latest_ms is None
    assert len(t.successful_latencies) == 2


def test_target_stats_all_timeouts():
    t = TargetStats(address="1.2.3.4", label="test")
    t.record(None)
    t.record(None)
    assert t.min_ms is None
    assert t.avg_ms is None
    assert t.max_ms is None
    assert t.loss_pct == 100.0


def test_target_stats_deque_maxlen():
    t = TargetStats(address="1.2.3.4", label="test")
    for i in range(100):
        t.record(float(i))
    assert len(t.history) == 60
    assert t.min_ms == 40.0
    assert t.max_ms == 99.0


def test_target_stats_single_value():
    t = TargetStats(address="1.2.3.4", label="test")
    t.record(42.0)
    assert t.min_ms == 42.0
    assert t.avg_ms == 42.0
    assert t.max_ms == 42.0
    assert t.loss_pct == 0.0
    assert t.latest_ms == 42.0
