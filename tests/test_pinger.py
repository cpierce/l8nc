"""Tests for the ping engine."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from l8nc.models import TargetStats
from l8nc.pinger import ping_loop, ping_once


@pytest.mark.asyncio
async def test_ping_once_returns_float_or_none():
    with patch("l8nc.pinger.ping_once_icmplib", new_callable=AsyncMock, return_value=15.0):
        result = await ping_once("127.0.0.1")
        assert result == 15.0


@pytest.mark.asyncio
async def test_ping_loop_count_exact():
    """ping_loop with count=5 should record exactly 5 results per target."""
    targets = [
        TargetStats(address="1.1.1.1", label="a"),
        TargetStats(address="8.8.8.8", label="b"),
    ]
    with patch("l8nc.pinger.ping_once", new_callable=AsyncMock, return_value=10.0):
        await ping_loop(targets, interval=0.01, count=5)

    for t in targets:
        assert len(t.history) == 5


@pytest.mark.asyncio
async def test_ping_loop_count_sets_stop_event():
    """ping_loop should set stop_event when count is reached."""
    targets = [TargetStats(address="1.1.1.1", label="a")]
    stop = asyncio.Event()

    with patch("l8nc.pinger.ping_once", new_callable=AsyncMock, return_value=10.0):
        await ping_loop(targets, interval=0.01, stop_event=stop, count=3)

    assert stop.is_set()
    assert len(targets[0].history) == 3


@pytest.mark.asyncio
async def test_ping_loop_stop_event_without_count():
    """ping_loop should stop when stop_event is set externally."""
    targets = [TargetStats(address="1.1.1.1", label="a")]
    stop = asyncio.Event()

    async def set_stop_after_delay():
        await asyncio.sleep(0.05)
        stop.set()

    with patch("l8nc.pinger.ping_once", new_callable=AsyncMock, return_value=10.0):
        await asyncio.gather(
            ping_loop(targets, interval=0.01, stop_event=stop),
            set_stop_after_delay(),
        )

    assert stop.is_set()
    assert len(targets[0].history) >= 1


@pytest.mark.asyncio
async def test_ping_loop_records_none_on_failure():
    """Timeouts should be recorded as None."""
    targets = [TargetStats(address="1.1.1.1", label="a")]

    with patch("l8nc.pinger.ping_once", new_callable=AsyncMock, return_value=None):
        await ping_loop(targets, interval=0.01, count=3)

    assert len(targets[0].history) == 3
    assert all(r.latency_ms is None for r in targets[0].history)
    assert targets[0].loss_pct == 100.0
