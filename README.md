# l8nc

Multi-target continuous ping monitor. Pings your gateway, ISP hop, and public DNS simultaneously, showing a live braille chart so you can instantly see *where* your internet is breaking.

Built for network engineers who need quick answers during calls.

## Install

```bash
pip install l8nc
```

## Usage

```bash
# Auto-detect gateway, ISP hop, and public DNS
l8nc

# Add custom targets to defaults
l8nc 10.0.0.1 example.com

# Only ping specified targets (skip auto-detection)
l8nc --only 10.0.0.1 example.com

# Limit to 10 pings
l8nc -c 10

# Save per-target CSV logs
l8nc -l logs/

# Replay chart from saved logs
l8nc --replay logs/
```

## What it does

l8nc auto-discovers three network hops and pings them in parallel:

1. **Gateway** — your local router
2. **ISP hop** — first hop outside your network (via traceroute)
3. **Public DNS** — Google (8.8.8.8) and Cloudflare (1.1.1.1)

All targets overlay on a single live chart. Timeouts show as `[DOWN]` rather than 0ms spikes, so the chart stays useful.

## Options

| Flag | Description |
|------|-------------|
| `-i`, `--interval` | Ping interval in seconds (default: 1) |
| `-c`, `--count` | Number of pings, then stop (default: infinite) |
| `-o`, `--only` | Only ping specified targets, skip auto-detection |
| `-l`, `--log` | Save per-target CSVs to a directory |
| `-r`, `--replay` | Replay a chart from a log directory |
| `-h`, `--help` | Show help |

## Requirements

- Python 3.8+
- macOS, Linux, or Windows

## License

MIT
