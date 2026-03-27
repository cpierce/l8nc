"""Async ping engine using icmplib with subprocess fallback."""

from __future__ import annotations

import asyncio
import re
import subprocess

from l8nc.models import TargetStats

# Try icmplib first, fall back to subprocess ping
try:
    from icmplib import async_ping as _icmplib_async_ping

    ICMPLIB_AVAILABLE = True
except ImportError:
    ICMPLIB_AVAILABLE = False


async def ping_once_icmplib(address: str, timeout: float) -> float | None:
    """Ping using icmplib. Returns latency in ms or None on failure."""
    try:
        result = await _icmplib_async_ping(
            address, count=1, interval=0, timeout=timeout, privileged=False
        )
        if result.is_alive:
            return result.avg_rtt
    except Exception:
        pass
    return None


async def ping_once_subprocess(address: str, timeout: float) -> float | None:
    """Ping using system ping command. Returns latency in ms or None on failure."""
    try:
        timeout_int = max(1, int(timeout))
        proc = await asyncio.create_subprocess_exec(
            "ping", "-c", "1", "-W", str(timeout_int), address,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout + 2)
        output = stdout.decode()
        match = re.search(r"time[=<](\d+\.?\d*)", output)
        if match:
            return float(match.group(1))
    except Exception:
        pass
    return None


async def ping_once(address: str, timeout: float = 2.0) -> float | None:
    """Ping a single address. Returns latency in ms or None."""
    if ICMPLIB_AVAILABLE:
        return await ping_once_icmplib(address, timeout)
    return await ping_once_subprocess(address, timeout)


async def ping_loop(
    targets: list[TargetStats],
    interval: float = 1.0,
    stop_event: asyncio.Event | None = None,
    count: int | None = None,
) -> None:
    """Continuously ping all targets in parallel."""
    pings_done = 0
    while True:
        if stop_event and stop_event.is_set():
            break

        tasks = [ping_once(t.address) for t in targets]
        results = await asyncio.gather(*tasks)

        for target, latency in zip(targets, results):
            target.record(latency)

        pings_done += 1
        if count is not None and pings_done >= count:
            if stop_event:
                stop_event.set()
            break

        if stop_event:
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=interval)
                break
            except asyncio.TimeoutError:
                pass
        else:
            await asyncio.sleep(interval)
