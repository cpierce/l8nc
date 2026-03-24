# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is l8nc?

l8nc is a multi-target continuous ping monitor CLI tool. It pings your gateway, ISP hop, and public DNS simultaneously, showing a live chart so you can instantly see *where* your internet is breaking. Built for network engineers who need quick answers during calls.

## Commands

```bash
# Install in editable mode
pip3 install -e .

# Run directly
python3 -m l8nc

# Run with options
python3 -m l8nc -c 10                    # 10 pings then stop
python3 -m l8nc 10.0.0.1 example.com     # add custom targets to defaults
python3 -m l8nc -o 8.8.8.8               # only ping specified targets
python3 -m l8nc -l logs/                  # enable per-target CSV logging
python3 -m l8nc --replay logs/            # replay chart from saved logs
```

## Architecture

The async event loop is the core — `cli.py:run()` manages three concurrent concerns:

1. **Pinger** (`pinger.py`) — `asyncio.gather()` pings all targets in parallel every interval. Uses `icmplib` with subprocess `ping` fallback.
2. **Display** (`display.py`) — `Rich.Live` updates a `plotext` braille chart at 2fps. All targets overlay on one chart. ANSI output from plotext is decoded via `rich.ansi.AnsiDecoder`.
3. **Logger** (`logger.py`) — Optional per-target CSV writer, only active with `-l` flag.

**Startup flow** in `cli.py:main()`:
- DNS preflight check → flags DNS as the problem immediately if broken
- Auto-discovery (gateway via `netstat`/`ip route`, ISP hop via traceroute, plus Google+Cloudflare DNS)
- Hostname resolution for custom targets, with reverse DNS on discovered IPs
- All discovery happens synchronously before the async loop starts

**Data model** (`models.py`): `TargetStats` holds a `deque(maxlen=60)` of `PingResult` objects. Stats (min/avg/max/loss) are computed properties over the rolling window.

All source lives under `src/l8nc/` (src layout).

**Replay** (`replay.py`): Reads CSV logs, detects session gaps (>3s between timestamps), draws vertical separator lines on the chart, and uses real timestamps on the X-axis.

## Key design decisions

- Custom targets **add to** defaults (use `--only` to skip defaults)
- Timeouts are excluded from the chart (not plotted as 0ms) — shown via `[DOWN]` status label instead
- Platform detection in `discovery.py` handles macOS/Linux/Windows differently
- `from __future__ import annotations` in all files for Python 3.9 compat with `X | Y` type hints
