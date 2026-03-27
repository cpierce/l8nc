"""Tests for CLI helpers."""

from __future__ import annotations

from unittest.mock import patch

from l8nc.cli import _is_ip, resolve_targets


def test_is_ip_valid():
    assert _is_ip("192.168.1.1") is True
    assert _is_ip("8.8.8.8") is True
    assert _is_ip("10.0.0.1") is True


def test_is_ip_invalid():
    assert _is_ip("example.com") is False
    assert _is_ip("not-an-ip") is False
    assert _is_ip("192.168.1") is False


def test_resolve_targets_ip():
    results = resolve_targets(("1.2.3.4",))
    assert len(results) == 1
    assert results[0].address == "1.2.3.4"
    assert results[0].label == "1.2.3.4"


def test_resolve_targets_hostname():
    with patch("l8nc.cli.resolve_hostname", return_value="93.184.216.34"):
        results = resolve_targets(("example.com",))
    assert len(results) == 1
    assert results[0].address == "93.184.216.34"
    assert results[0].label == "example.com"


def test_resolve_targets_unresolvable():
    with patch("l8nc.cli.resolve_hostname", return_value=None):
        results = resolve_targets(("bad.invalid",))
    assert len(results) == 0
