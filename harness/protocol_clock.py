"""Monotonic episode clock with separately accounted infrastructure downtime."""

from __future__ import annotations

import time
from typing import Callable


class WallClockExpired(RuntimeError):
    """Infrastructure delays exhausted the protective wall-clock budget."""


class EffectiveClockExpired(RuntimeError):
    """The episode's usable time budget expired."""


class ProtocolClock:
    def __init__(self, seconds: float, now: Callable[[], float] = time.monotonic):
        if seconds <= 0:
            raise ValueError("时间预算必须大于零")
        self.limit = float(seconds)
        self.now = now
        self.started = now()
        self.paused = 0.0

    @property
    def wall(self) -> float:
        return max(0.0, self.now() - self.started)

    @property
    def effective(self) -> float:
        return max(0.0, self.wall - self.paused)

    def add_infrastructure_delay(self, seconds: float) -> None:
        self.paused += max(0.0, seconds)

    def check(self) -> None:
        if self.wall >= 2 * self.limit:
            raise WallClockExpired("墙钟保护上限已用尽")
        if self.effective >= self.limit:
            raise EffectiveClockExpired("有效时间预算已用尽")

    def timeout(self, maximum: float) -> float:
        self.check()
        return min(maximum, self.limit - self.effective, 2 * self.limit - self.wall)
