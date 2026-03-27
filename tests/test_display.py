"""Tests for the display module."""

from __future__ import annotations

from rich.console import Group

from l8nc.display import build_display, _fmt_ms, _status_label, _status_color
from l8nc.models import TargetStats


def test_fmt_ms_none():
    assert _fmt_ms(None) == "--"


def test_fmt_ms_value():
    assert _fmt_ms(15.123) == "15.1ms"


def test_fmt_ms_zero():
    assert _fmt_ms(0.0) == "0.0ms"


def test_status_label_waiting():
    t = TargetStats(address="1.1.1.1", label="test")
    label, style = _status_label(t)
    assert label == "WAITING"


def test_status_label_ok():
    t = TargetStats(address="1.1.1.1", label="test")
    t.record(10.0)
    label, _ = _status_label(t)
    assert label == "OK"


def test_status_label_no_reply():
    t = TargetStats(address="1.1.1.1", label="test")
    t.record(None)
    label, _ = _status_label(t)
    assert label == "NO REPLY"


def test_status_label_dropping():
    t = TargetStats(address="1.1.1.1", label="test")
    for i in range(20):
        t.record(10.0)
    t.record(None)  # 1/21 ~ 4.8% loss, but latest is None
    # Latest ping is timeout, so most recent 5 check triggers NO REPLY first
    # To get DROPPING, last ping must succeed but have some loss in window
    t.record(10.0)  # now latest is OK, 1/22 ~ 4.5% loss
    label, _ = _status_label(t)
    assert label == "DROPPING"


def test_status_color_green():
    t = TargetStats(address="1.1.1.1", label="test")
    t.record(10.0)
    assert _status_color(t) == "green"


def test_status_color_yellow_high_latency():
    t = TargetStats(address="1.1.1.1", label="test")
    t.record(150.0)
    assert _status_color(t) == "yellow"


def test_status_color_red_high_loss():
    t = TargetStats(address="1.1.1.1", label="test")
    for _ in range(5):
        t.record(10.0)
    for _ in range(5):
        t.record(None)
    # 50% loss
    assert _status_color(t) == "red"


def test_build_display_empty():
    targets = [TargetStats(address="1.1.1.1", label="test")]
    result = build_display(targets)
    assert isinstance(result, Group)


def test_build_display_with_data():
    targets = [TargetStats(address="1.1.1.1", label="test")]
    targets[0].record(15.0)
    targets[0].record(20.0)
    result = build_display(targets)
    assert isinstance(result, Group)


def test_build_display_multiple_targets():
    targets = [
        TargetStats(address="1.1.1.1", label="a"),
        TargetStats(address="8.8.8.8", label="b"),
    ]
    for t in targets:
        t.record(10.0)
        t.record(20.0)
    result = build_display(targets)
    assert isinstance(result, Group)
