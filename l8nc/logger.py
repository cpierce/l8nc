"""Automatic per-target logging to logs/ directory."""

from __future__ import annotations

import csv
import datetime
import os
import re

from l8nc.models import TargetStats


def _safe_filename(name: str) -> str:
    """Convert a label to a safe filename."""
    name = re.sub(r"[^\w\-.]", "_", name)
    name = re.sub(r"_+", "_", name).strip("_")
    return name or "unknown"


class LogManager:
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        self._files: dict[str, str] = {}  # address -> filepath
        self._initialized: set[str] = set()

    def _ensure_dir(self) -> None:
        os.makedirs(self.log_dir, exist_ok=True)

    def _get_path(self, target: TargetStats) -> str:
        if target.address not in self._files:
            filename = _safe_filename(target.label) + ".csv"
            self._files[target.address] = os.path.join(self.log_dir, filename)
        return self._files[target.address]

    def _init_file(self, target: TargetStats) -> None:
        """Write header if this is a new session (append with session marker)."""
        if target.address in self._initialized:
            return

        self._ensure_dir()
        path = self._get_path(target)
        file_exists = os.path.exists(path) and os.path.getsize(path) > 0

        with open(path, "a", newline="") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["timestamp", "latency_ms", "loss_pct", "min_ms", "avg_ms", "max_ms", "status"])
            else:
                # Session separator
                writer.writerow([])
                writer.writerow([f"# session started {datetime.datetime.now().isoformat()}"])

        self._initialized.add(target.address)

    def write(self, targets: list[TargetStats]) -> None:
        """Write one row per target to its log file."""
        for t in targets:
            if not t.history:
                continue

            self._init_file(t)
            path = self._get_path(t)

            latest = t.latest_ms
            status = "ok" if latest is not None else "timeout"

            with open(path, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.datetime.now().isoformat(),
                    f"{latest:.1f}" if latest is not None else "",
                    f"{t.loss_pct:.1f}",
                    f"{t.min_ms:.1f}" if t.min_ms is not None else "",
                    f"{t.avg_ms:.1f}" if t.avg_ms is not None else "",
                    f"{t.max_ms:.1f}" if t.max_ms is not None else "",
                    status,
                ])

    def summary(self) -> dict[str, str]:
        """Return {label: filepath} for all log files written."""
        return {addr: path for addr, path in self._files.items() if addr in self._initialized}
