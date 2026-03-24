"""Replay logged data as a chart."""

from __future__ import annotations

import csv
import os
from datetime import datetime

import plotext as plt
from rich.ansi import AnsiDecoder
from rich.console import Console
from rich.text import Text

PLOT_COLORS = ["blue", "green", "red", "yellow", "cyan", "magenta"]

console = Console()

# Minimum gap in seconds to consider a session break
SESSION_GAP_THRESHOLD = 3.0


def _parse_logs(log_dir: str) -> tuple[list[dict], list[float]]:
    """Read all CSV logs. Returns (targets, session_break_times).

    session_break_times are epoch timestamps where gaps > threshold were found.
    """
    csv_files = sorted(f for f in os.listdir(log_dir) if f.endswith(".csv"))
    targets = []
    all_break_times: set[float] = set()

    for filename in csv_files:
        filepath = os.path.join(log_dir, filename)
        label = filename.replace(".csv", "")

        timestamps = []
        latencies = []
        timeouts = 0
        total = 0
        prev_ts = None

        with open(filepath, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                ts_str = row.get("timestamp", "")
                if not ts_str or ts_str.startswith("#"):
                    continue
                total += 1
                try:
                    ts = datetime.fromisoformat(ts_str)
                except ValueError:
                    continue

                # Detect gaps between data points
                if prev_ts is not None:
                    gap = (ts - prev_ts).total_seconds()
                    if gap > SESSION_GAP_THRESHOLD:
                        # Mark the midpoint of the gap as a session break
                        mid = prev_ts.timestamp() + gap / 2
                        all_break_times.add(mid)
                prev_ts = ts

                lat = row.get("latency_ms", "")
                if lat and lat != "":
                    try:
                        timestamps.append(ts)
                        latencies.append(float(lat))
                    except ValueError:
                        timeouts += 1
                else:
                    timeouts += 1

        if timestamps:
            targets.append({
                "label": label,
                "timestamps": timestamps,
                "latencies": latencies,
                "timeouts": timeouts,
                "total": total,
            })

    # Deduplicate breaks that are close together (within threshold)
    sorted_breaks = sorted(all_break_times)
    deduped = []
    for bt in sorted_breaks:
        if not deduped or (bt - deduped[-1]) > SESSION_GAP_THRESHOLD:
            deduped.append(bt)

    return targets, deduped


def _format_duration(start: datetime, end: datetime) -> str:
    """Format the time span of the data."""
    delta = end - start
    seconds = int(delta.total_seconds())
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        return f"{seconds // 60}m {seconds % 60}s"
    hours = seconds // 3600
    mins = (seconds % 3600) // 60
    if hours < 24:
        return f"{hours}h {mins}m"
    days = hours // 24
    hours = hours % 24
    return f"{days}d {hours}h"


def replay_logs(log_dir: str) -> None:
    """Read all CSV logs from a directory and render a combined chart."""
    if not os.path.isdir(log_dir):
        console.print(f"[red]  Directory not found: {log_dir}[/]")
        return

    targets, break_times = _parse_logs(log_dir)
    if not targets:
        console.print(f"[red]  No log data found in {log_dir}/[/]")
        return

    # Find overall time range
    all_timestamps = []
    for t in targets:
        all_timestamps.extend(t["timestamps"])
    earliest = min(all_timestamps)
    latest = max(all_timestamps)
    duration = _format_duration(earliest, latest)
    num_sessions = len(break_times) + 1

    console.print(f"[bold cyan]l8nc[/] — replay from [bold]{log_dir}/[/]")
    console.print(f"  {earliest.strftime('%Y-%m-%d %H:%M')} → {latest.strftime('%Y-%m-%d %H:%M')} ({duration})")
    console.print(f"  {num_sessions} session{'s' if num_sessions > 1 else ''}")
    console.print()

    plt.clear_figure()
    plt.theme("dark")

    origin = earliest.timestamp()

    for i, t in enumerate(targets):
        label = t["label"]
        latencies = t["latencies"]
        timestamps = t["timestamps"]
        timeouts = t["timeouts"]
        total = t["total"]
        plot_color = PLOT_COLORS[i % len(PLOT_COLORS)]

        min_ms = min(latencies)
        avg_ms = sum(latencies) / len(latencies)
        max_ms = max(latencies)
        loss_pct = (timeouts / total * 100) if total > 0 else 0

        line = Text()
        line.append(f" ■ ", style=f"bold {plot_color}")
        line.append(f"{label}", style="bold white")
        line.append(f"  min {min_ms:.1f}ms", style="dim")
        line.append(f"  avg {avg_ms:.1f}ms", style="dim")
        line.append(f"  max {max_ms:.1f}ms", style="dim")
        line.append(f"  loss {loss_pct:.0f}%", style="bold red" if loss_pct > 0 else "green")
        line.append(f"  ({total} pings)", style="dim")
        console.print(line)

        # Seconds since start of recording
        x_vals = [ts.timestamp() - origin for ts in timestamps]
        plt.plot(x_vals, latencies, marker="braille", color=plot_color)

    # Draw vertical lines at session breaks
    all_latencies = []
    for t in targets:
        all_latencies.extend(t["latencies"])
    y_min = min(all_latencies) if all_latencies else 0
    y_max = max(all_latencies) if all_latencies else 1

    # Add some padding to vertical lines so they extend beyond data
    y_padding = (y_max - y_min) * 0.05
    for idx, bt in enumerate(break_times):
        x_pos = bt - origin
        # Draw vertical line with many points so it's solid
        steps = 20
        y_points = [y_min - y_padding + (y_max - y_min + 2 * y_padding) * s / steps for s in range(steps + 1)]
        x_points = [x_pos] * len(y_points)
        plt.plot(x_points, y_points, marker="braille", color="gray")

    # Build custom X-axis ticks showing real timestamps
    total_secs = latest.timestamp() - origin
    num_ticks = 5
    tick_positions = []
    tick_labels = []
    for j in range(num_ticks):
        pos = total_secs * j / (num_ticks - 1) if total_secs > 0 else 0
        tick_positions.append(pos)
        ts = datetime.fromtimestamp(origin + pos)
        if (latest - earliest).days >= 1:
            tick_labels.append(ts.strftime("%m/%d %H:%M"))
        else:
            tick_labels.append(ts.strftime("%H:%M:%S"))

    plt.xticks(tick_positions, tick_labels)

    plt.plotsize(80, 18)
    plt.ylabel("ms")
    plt.xlabel("")
    plt.title("")

    console.print()
    plot_str = plt.build()
    decoder = AnsiDecoder()
    for line in decoder.decode(plot_str):
        console.print(line)

    # Show session break details using break_times to split
    if break_times:
        console.print()
        console.print("[dim]  Sessions:[/]")

        # Collect all timestamps across all targets, sorted
        every_ts = sorted(all_timestamps)

        # Split into sessions using break_times as dividers
        sessions = []
        current = []
        break_set = list(break_times)
        bi = 0
        for ts in every_ts:
            epoch = ts.timestamp()
            if bi < len(break_set) and epoch > break_set[bi]:
                if current:
                    sessions.append(current)
                current = []
                bi += 1
            current.append(ts)
        if current:
            sessions.append(current)

        for s, sess_timestamps in enumerate(sessions):
            start = min(sess_timestamps)
            end = max(sess_timestamps)
            dur = _format_duration(start, end)
            console.print(f"    Session {s + 1}: {start.strftime('%H:%M:%S')} → {end.strftime('%H:%M:%S')} ({dur})")
            if s < len(sessions) - 1:
                next_start = min(sessions[s + 1])
                gap_dur = _format_duration(end, next_start)
                console.print(f"    [dim]  ↕ gap: {gap_dur}[/]")
