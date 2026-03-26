"""Rich TUI display for live ping results."""

from __future__ import annotations

import plotext as plt
from rich.ansi import AnsiDecoder
from rich.console import Group
from rich.live import Live
from rich.text import Text

from l8nc.models import TargetStats


PLOT_COLORS = ["blue", "green", "red", "yellow", "cyan", "magenta"]


def _status_color(t: TargetStats) -> str:
    if t.loss_pct > 10:
        return "red"
    if t.loss_pct > 0:
        return "yellow"
    if t.max_ms and t.max_ms > 100:
        return "yellow"
    return "green"


def _status_label(t: TargetStats) -> tuple[str, str]:
    """Return (label, color) for current target status."""
    if not t.history:
        return "WAITING", "dim"
    if t.latest_ms is None:
        return "NO REPLY", "bold red"
    # Check if last N pings all failed
    recent = list(t.history)[-5:]
    if all(r.latency_ms is None for r in recent):
        return "NO REPLY", "bold red"
    if t.loss_pct > 50:
        return "FAILING", "bold red"
    if t.loss_pct > 10:
        return "UNSTABLE", "bold yellow"
    if t.loss_pct > 0:
        return "DROPPING", "yellow"
    return "OK", "green"


def _fmt_ms(ms: float | None) -> str:
    if ms is None:
        return "--"
    return f"{ms:.1f}ms"


def build_display(targets: list[TargetStats]) -> Group:
    """Build a single chart with all targets overlaid."""
    # Stats header per target
    stats_lines = []
    for i, t in enumerate(targets):
        color = _status_color(t)
        now_str = _fmt_ms(t.latest_ms)
        loss_str = f"{t.loss_pct:.0f}%"
        plot_color = PLOT_COLORS[i % len(PLOT_COLORS)]
        status_text, status_style = _status_label(t)

        line = Text()
        line.append(f" ■ ", style=f"bold {plot_color}")
        line.append(f"{t.label} ({t.address})", style="bold white")
        line.append(f"  [{status_text}]", style=status_style)
        line.append(f"  {now_str}", style=f"bold {color}")
        line.append("  ", style="dim")
        line.append(f"min {_fmt_ms(t.min_ms)}", style="dim")
        line.append(f"  avg {_fmt_ms(t.avg_ms)}", style="dim")
        line.append(f"  max {_fmt_ms(t.max_ms)}", style="dim")
        line.append(f"  loss {loss_str}", style=f"bold {color}")
        stats_lines.append(line)

    # Build combined plot — only plot successful pings
    plt.clear_figure()
    plt.theme("dark")

    has_data = False
    for i, t in enumerate(targets):
        results = list(t.history)
        # Use None gaps for timeouts so the line breaks
        x_vals = []
        y_vals = []
        for j, r in enumerate(results):
            if r.latency_ms is not None:
                x_vals.append(j + 1)
                y_vals.append(r.latency_ms)

        if y_vals:
            has_data = True
            plot_color = PLOT_COLORS[i % len(PLOT_COLORS)]
            label = t.label
            plt.plot(x_vals, y_vals, marker="braille", color=plot_color)

    plt.plotsize(80, 18)
    plt.ylabel("ms")
    plt.xlabel("")
    plt.title("")

    parts = []
    title = Text("l8nc", style="bold cyan")
    hint = Text("  Ctrl+C to stop", style="dim")
    parts.extend([title, hint, Text("")])
    parts.extend(stats_lines)
    parts.append(Text(""))

    if has_data:
        plot_str = plt.build()
        decoder = AnsiDecoder()
        plot_lines = list(decoder.decode(plot_str))
        parts.extend(plot_lines)
    else:
        parts.append(Text("  Waiting for data...", style="dim"))

    return Group(*parts)


def create_live_display() -> Live:
    """Create a Rich Live context manager for the TUI."""
    return Live(refresh_per_second=2, transient=False)
