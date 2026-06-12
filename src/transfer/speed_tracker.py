"""
TurboShare — Rolling-average speed tracker and ETA calculator.

Records bytes transferred over time and computes a rolling average
over the last 2 seconds.  Updated every second for display.
"""

import time
import collections
from dataclasses import dataclass


@dataclass
class SpeedSnapshot:
    """A single measurement."""
    timestamp: float
    bytes_count: int


class SpeedTracker:
    """Tracks transfer speed using a rolling window."""

    def __init__(self, window_seconds: float = 2.0) -> None:
        self.window = window_seconds
        self._samples: collections.deque[SpeedSnapshot] = collections.deque()
        self._total_bytes: int = 0
        self._start_time: float = 0.0

    def start(self) -> None:
        self._start_time = time.monotonic()
        self._samples.clear()
        self._total_bytes = 0

    def record(self, bytes_count: int) -> None:
        """Record that *bytes_count* bytes were just transferred."""
        now = time.monotonic()
        self._samples.append(SpeedSnapshot(now, bytes_count))
        self._total_bytes += bytes_count
        self._prune(now)

    def _prune(self, now: float) -> None:
        cutoff = now - self.window
        while self._samples and self._samples[0].timestamp < cutoff:
            self._samples.popleft()

    @property
    def speed_bytes_per_sec(self) -> float:
        """Current speed in bytes/s (rolling average)."""
        if not self._samples:
            return 0.0
        now = time.monotonic()
        self._prune(now)
        if not self._samples:
            return 0.0
        window_bytes = sum(s.bytes_count for s in self._samples)
        elapsed = now - self._samples[0].timestamp
        if elapsed <= 0:
            return 0.0
        return window_bytes / elapsed

    @property
    def speed_mbps(self) -> float:
        """Current speed in MB/s."""
        return self.speed_bytes_per_sec / (1024 * 1024)

    def eta_seconds(self, remaining_bytes: int) -> float:
        """Estimated seconds to finish, or -1 if speed is zero."""
        spd = self.speed_bytes_per_sec
        if spd <= 0:
            return -1.0
        return remaining_bytes / spd

    @property
    def average_speed_mbps(self) -> float:
        """Overall average speed since start()."""
        if self._start_time <= 0:
            return 0.0
        elapsed = time.monotonic() - self._start_time
        if elapsed <= 0:
            return 0.0
        return (self._total_bytes / elapsed) / (1024 * 1024)

    @property
    def total_bytes(self) -> int:
        return self._total_bytes

    @property
    def elapsed_seconds(self) -> float:
        if self._start_time <= 0:
            return 0.0
        return time.monotonic() - self._start_time
