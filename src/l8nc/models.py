"""Data classes for ping results and target statistics."""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field


@dataclass
class PingResult:
    timestamp: float
    latency_ms: float | None  # None = timeout/loss

    @property
    def is_success(self) -> bool:
        return self.latency_ms is not None


@dataclass
class TargetStats:
    address: str
    label: str
    history: deque[PingResult] = field(default_factory=lambda: deque(maxlen=60))

    def record(self, latency_ms: float | None) -> None:
        self.history.append(PingResult(timestamp=time.time(), latency_ms=latency_ms))

    @property
    def successful_latencies(self) -> list[float]:
        return [r.latency_ms for r in self.history if r.is_success]

    @property
    def min_ms(self) -> float | None:
        lats = self.successful_latencies
        return min(lats) if lats else None

    @property
    def avg_ms(self) -> float | None:
        lats = self.successful_latencies
        return sum(lats) / len(lats) if lats else None

    @property
    def max_ms(self) -> float | None:
        lats = self.successful_latencies
        return max(lats) if lats else None

    @property
    def loss_pct(self) -> float:
        if not self.history:
            return 0.0
        lost = sum(1 for r in self.history if not r.is_success)
        return (lost / len(self.history)) * 100

    @property
    def latest_ms(self) -> float | None:
        if not self.history:
            return None
        return self.history[-1].latency_ms

    def ascii_chart(self, width: int = 50, height: int = 6) -> list[str]:
        """Draw a plain ASCII line chart.

        Returns a list of strings (one per row). Uses /, \\, _, ─ to
        draw a line you can actually read.
        """
        results = list(self.history)[-width:]
        if not results:
            return []

        values = []
        for r in results:
            values.append(r.latency_ms)

        successful = [v for v in values if v is not None]
        if not successful:
            return [" X" * len(values)]

        lo = min(successful)
        hi = max(successful)
        if hi == lo:
            # Flat line — center it
            lo = lo - 1 if lo > 1 else 0
            hi = hi + 1
        span = hi - lo

        # Map each value to a row (0 = bottom, height-1 = top)
        mapped = []
        for v in values:
            if v is None:
                mapped.append(-1)
            else:
                row = int((v - lo) / span * (height - 1) + 0.5)
                row = max(0, min(height - 1, row))
                mapped.append(row)

        # Build grid: grid[row][col], row 0 = bottom
        grid = [[" "] * len(mapped) for _ in range(height)]

        for col in range(len(mapped)):
            val = mapped[col]
            if val == -1:
                grid[0][col] = "X"
                continue

            if col == 0:
                # First point — just place it
                grid[val][col] = "─"
                continue

            prev = mapped[col - 1]
            if prev == -1:
                grid[val][col] = "─"
                continue

            if val == prev:
                # Flat — horizontal line
                grid[val][col] = "─"
            elif val > prev:
                # Going up — draw / from prev+1 to val
                grid[prev][col - 1] = grid[prev][col - 1] if grid[prev][col - 1] != " " else "─"
                for r in range(prev + 1, val + 1):
                    grid[r][col] = "/"
            else:
                # Going down — draw \ from prev-1 to val
                grid[prev][col - 1] = grid[prev][col - 1] if grid[prev][col - 1] != " " else "─"
                for r in range(val, prev):
                    grid[r][col] = "\\"

        # Build output with Y-axis labels
        step = span / (height - 1) if height > 1 else span
        rows = []
        for r in range(height - 1, -1, -1):
            ms = lo + step * r
            label = f"{ms:>5.0f}ms"
            line = "".join(grid[r])
            rows.append(f"{label} ┤{line}")

        return rows
