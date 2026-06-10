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


def test_session_counters_outlive_rolling_window():
    """total_pings must keep growing after the history deque is full —
    the live loop keys CSV logging off it."""
    t = TargetStats(address="1.2.3.4", label="test")
    for i in range(100):
        t.record(float(i))
    assert len(t.history) == 60
    assert t.total_pings == 100
    # Session stats cover all 100 pings, not just the window
    assert t.session_min_ms == 0.0
    assert t.session_max_ms == 99.0
    assert t.session_avg_ms == 49.5


def test_session_loss_counters():
    t = TargetStats(address="1.2.3.4", label="test")
    t.record(10.0)
    t.record(None)
    t.record(None)
    t.record(30.0)
    assert t.total_pings == 4
    assert t.total_lost == 2
    assert t.session_loss_pct == 50.0
    assert t.session_avg_ms == 20.0


def test_session_stats_empty():
    t = TargetStats(address="1.2.3.4", label="test")
    assert t.total_pings == 0
    assert t.session_loss_pct == 0.0
    assert t.session_avg_ms is None
    assert t.session_min_ms is None
    assert t.session_max_ms is None


def test_jitter():
    t = TargetStats(address="1.2.3.4", label="test")
    t.record(10.0)
    t.record(20.0)
    t.record(14.0)
    # diffs: |20-10|=10, |14-20|=6 → mean 8
    assert t.jitter_ms == 8.0


def test_jitter_needs_two_samples():
    t = TargetStats(address="1.2.3.4", label="test")
    assert t.jitter_ms is None
    t.record(10.0)
    assert t.jitter_ms is None
    t.record(None)
    assert t.jitter_ms is None  # timeouts don't count


def test_jitter_skips_timeouts():
    t = TargetStats(address="1.2.3.4", label="test")
    t.record(10.0)
    t.record(None)
    t.record(20.0)
    assert t.jitter_ms == 10.0


def test_target_stats_single_value():
    t = TargetStats(address="1.2.3.4", label="test")
    t.record(42.0)
    assert t.min_ms == 42.0
    assert t.avg_ms == 42.0
    assert t.max_ms == 42.0
    assert t.loss_pct == 0.0
    assert t.latest_ms == 42.0
