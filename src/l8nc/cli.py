"""CLI entry point for l8nc."""

from __future__ import annotations

import asyncio
import re
import signal

import click
from rich.console import Console

from l8nc.discovery import check_dns, discover_targets, resolve_hostname
from l8nc.display import build_display, create_live_display
from l8nc.logger import LogManager
from l8nc.models import TargetStats
from l8nc.pinger import ping_loop
from l8nc.replay import replay_logs


console = Console()


def _is_ip(address: str) -> bool:
    return bool(re.match(r"^\d+\.\d+\.\d+\.\d+$", address))


def resolve_targets(raw_targets: tuple[str, ...]) -> list[TargetStats]:
    """Resolve hostnames to IPs up front. Warn on failures."""
    stats = []
    for t in raw_targets:
        if _is_ip(t):
            stats.append(TargetStats(address=t, label=t))
        else:
            ip = resolve_hostname(t)
            if ip:
                stats.append(TargetStats(address=ip, label=t))
                console.print(f"  [green]✓[/] {t} → {ip}")
            else:
                console.print(f"  [red]✗[/] {t} — could not resolve (skipping)")
    return stats


async def run(
    targets: list[TargetStats],
    interval: float,
    count: int | None,
    log_dir: str | None,
) -> None:
    stop_event = asyncio.Event()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop_event.set)

    logger = LogManager(log_dir=log_dir) if log_dir else None

    ping_task = asyncio.create_task(
        ping_loop(targets, interval=interval, stop_event=stop_event, count=count)
    )

    last_history_len = 0
    with create_live_display() as live:
        while not stop_event.is_set():
            live.update(build_display(targets))

            # Only log when new ping data arrives
            if logger:
                cur_len = sum(len(t.history) for t in targets)
                if cur_len > last_history_len:
                    logger.write(targets)
                    last_history_len = cur_len

            try:
                await asyncio.wait_for(stop_event.wait(), timeout=0.5)
            except asyncio.TimeoutError:
                pass

        # Final display update to show all data
        live.update(build_display(targets))

    await ping_task

    # Print summary
    console.print()
    console.print("[bold cyan]── Summary ──[/]")
    for t in targets:
        min_str = f"{t.min_ms:.1f}ms" if t.min_ms is not None else "--"
        avg_str = f"{t.avg_ms:.1f}ms" if t.avg_ms is not None else "--"
        max_str = f"{t.max_ms:.1f}ms" if t.max_ms is not None else "--"
        total = len(t.history)
        lost = sum(1 for r in t.history if not r.is_success)
        console.print(
            f"  {t.label} ({t.address}): "
            f"{min_str}/{avg_str}/{max_str} "
            f"loss={t.loss_pct:.1f}% ({lost}/{total})"
        )

    if logger:
        console.print()
        console.print("[bold cyan]── Logs ──[/]")
        for addr, path in logger.summary().items():
            console.print(f"  {path}")


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(None, "-v", "--version", package_name="l8nc", prog_name="l8nc", message="%(prog)s %(version)s")
@click.argument("targets", nargs=-1)
@click.option("--interval", "-i", default=1.0, help="Ping interval in seconds.")
@click.option("--count", "-c", default=None, type=int, help="Number of pings (default: infinite).")
@click.option("--log", "-l", default=None, type=click.Path(), help="Enable logging. Saves per-target CSVs to this directory.")
@click.option("--only", "-o", is_flag=True, help="Only ping the specified targets (skip auto-detected defaults).")
@click.option("--replay", "-r", default=None, type=click.Path(exists=True), help="Replay a chart from a log directory.")
def main(targets: tuple[str, ...], interval: float, count: int | None, log: str | None, only: bool, replay: str | None) -> None:
    """Multi-target continuous ping monitor.

    Run with no arguments to auto-detect gateway, ISP hop, and public DNS.
    Pass additional targets to add them to the defaults:

        l8nc 10.0.0.1 example.com

    Use --only to skip defaults and only ping what you specify:

        l8nc --only 10.0.0.1 example.com

    Use -l to save per-target logs:

        l8nc -l logs/

    Replay from saved logs:

        l8nc --replay logs/
    """
    if replay:
        replay_logs(replay)
        return
    console.print("[bold cyan]l8nc[/]")
    console.print()

    # DNS preflight check
    console.print("  Checking DNS...")
    if not check_dns():
        console.print()
        console.print("[bold red]  ✗ DNS is not working![/]")
        console.print("    Could not resolve any test domains (google.com, cloudflare.com, amazon.com)")
        console.print("    This is likely your problem. Check:")
        console.print("      • Your DNS server settings (/etc/resolv.conf or network config)")
        console.print("      • Whether your router/gateway is reachable")
        console.print("      • Whether your ISP's DNS servers are down")
        console.print()
        console.print("    Falling back to IP-only targets...\n")
    else:
        console.print("  [green]✓[/] DNS is working\n")

    stats = []

    if not only:
        console.print("  Discovering network targets...")
        discovered = discover_targets()
        if discovered:
            stats = [TargetStats(address=addr, label=label) for addr, label in discovered]
            for s in stats:
                console.print(f"  [green]✓[/] {s.label} → {s.address}")
        console.print()

    if targets:
        console.print("  Resolving custom targets...")
        custom = resolve_targets(targets)
        existing = {s.address for s in stats}
        for s in custom:
            if s.address not in existing:
                stats.append(s)
                existing.add(s.address)
        console.print()

    if not stats:
        console.print("[red]  No targets to monitor.[/]")
        raise SystemExit(1)

    if log:
        console.print(f"  Logging to [bold]{log}/[/]")
    console.print("  Press [bold]Ctrl+C[/] to stop.\n")

    asyncio.run(run(stats, interval=interval, count=count, log_dir=log))
