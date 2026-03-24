"""Auto-detect network targets: gateway and ISP upstream hop."""

from __future__ import annotations

import platform
import re
import socket
import subprocess

from rich.console import Console

console = Console()


def check_dns() -> bool:
    """Quick DNS health check. Returns True if DNS is working."""
    test_hosts = ["google.com", "cloudflare.com", "amazon.com"]
    for host in test_hosts:
        try:
            socket.getaddrinfo(host, None, socket.AF_INET, socket.SOCK_STREAM)
            return True
        except socket.gaierror:
            continue
    return False


def resolve_hostname(hostname: str) -> str | None:
    """Resolve a hostname to an IP. Returns None on failure."""
    try:
        results = socket.getaddrinfo(hostname, None, socket.AF_INET, socket.SOCK_STREAM)
        if results:
            return results[0][4][0]
    except socket.gaierror:
        pass
    return None


def reverse_dns(ip: str) -> str | None:
    """Try reverse DNS on an IP. Returns hostname or None."""
    try:
        hostname, _, _ = socket.gethostbyaddr(ip)
        # Don't return if it's just the IP repeated or too long
        if hostname and hostname != ip and len(hostname) < 60:
            return hostname
    except (socket.herror, socket.gaierror, OSError):
        pass
    return None


def get_default_gateway() -> str | None:
    """Detect the default gateway IP address."""
    system = platform.system()
    try:
        if system == "Darwin":
            out = subprocess.check_output(
                ["netstat", "-nr"], text=True, timeout=5
            )
            for line in out.splitlines():
                parts = line.split()
                if len(parts) >= 2 and parts[0] == "default":
                    ip = parts[1]
                    if re.match(r"\d+\.\d+\.\d+\.\d+", ip):
                        return ip
        elif system == "Linux":
            out = subprocess.check_output(
                ["ip", "route", "show", "default"], text=True, timeout=5
            )
            match = re.search(r"via\s+(\d+\.\d+\.\d+\.\d+)", out)
            if match:
                return match.group(1)
        else:
            out = subprocess.check_output(
                ["ipconfig"], text=True, timeout=5
            )
            match = re.search(r"Default Gateway.*?:\s*(\d+\.\d+\.\d+\.\d+)", out)
            if match:
                return match.group(1)
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    return None


def get_upstream_hop() -> str | None:
    """Get the first hop after the gateway (ISP upstream)."""
    try:
        cmd = ["traceroute", "-n", "-m", "3", "-q", "1", "-w", "2", "8.8.8.8"]
        out = subprocess.check_output(
            cmd, text=True, timeout=15, stderr=subprocess.DEVNULL
        )
        hops = []
        for line in out.splitlines():
            match = re.match(r"\s*\d+\s+(\d+\.\d+\.\d+\.\d+)", line)
            if match:
                hops.append(match.group(1))

        if len(hops) >= 2:
            return hops[1]
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    return None


def discover_targets() -> list[tuple[str, str]]:
    """Return list of (address, label) for default targets."""
    targets = []

    gw = get_default_gateway()
    if gw:
        rdns = reverse_dns(gw)
        label = f"gateway ({rdns})" if rdns else "gateway"
        targets.append((gw, label))

    upstream = get_upstream_hop()
    if upstream:
        rdns = reverse_dns(upstream)
        label = f"isp ({rdns})" if rdns else "isp"
        targets.append((upstream, label))

    targets.append(("8.8.8.8", "google-dns"))
    targets.append(("1.1.1.1", "cloudflare"))

    return targets
