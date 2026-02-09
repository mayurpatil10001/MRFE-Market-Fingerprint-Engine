"""Continuous learning primitives for incremental adaptation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Iterable


@dataclass(frozen=True, slots=True)
class RegimeState:
    """Detected market regime state."""

    regime: str
    volatility_score: float
    trend_score: float
    detected_at: datetime


class IncrementalLearner:
    """Simple online centroid learner for fingerprint vectors."""

    def __init__(self, dimension: int) -> None:
        self._dimension = dimension
        self._centroid = [0.0] * dimension
        self._observations = 0
        self._last_updated: datetime | None = None

    @property
    def observations(self) -> int:
        """Number of samples incorporated so far."""
        return self._observations

    @property
    def centroid(self) -> list[float]:
        """Current centroid estimate."""
        return list(self._centroid)

    @property
    def last_updated(self) -> datetime | None:
        """Last update time."""
        return self._last_updated

    def update(self, vector: Iterable[float]) -> list[float]:
        """Update centroid with one new observation."""
        values = [float(value) for value in vector]
        if len(values) != self._dimension:
            raise ValueError(f"expected vector of size {self._dimension}")
        self._observations += 1
        rate = 1.0 / self._observations
        self._centroid = [
            (1 - rate) * current + rate * new
            for current, new in zip(self._centroid, values, strict=True)
        ]
        self._last_updated = datetime.now(tz=UTC)
        return self.centroid


class RegimeDetector:
    """Detect simple bull/bear/volatile regimes from rolling returns."""

    def detect(self, returns: list[float]) -> RegimeState:
        """Classify regime using trend and realized volatility."""
        if not returns:
            return RegimeState(
                regime="unknown",
                volatility_score=0.0,
                trend_score=0.0,
                detected_at=datetime.now(tz=UTC),
            )
        trend = sum(returns) / len(returns)
        variance = sum((value - trend) ** 2 for value in returns) / len(returns)
        volatility = variance ** 0.5
        if volatility > 0.03:
            regime = "volatile"
        elif trend > 0.001:
            regime = "bull"
        elif trend < -0.001:
            regime = "bear"
        else:
            regime = "sideways"
        return RegimeState(
            regime=regime,
            volatility_score=round(volatility, 6),
            trend_score=round(trend, 6),
            detected_at=datetime.now(tz=UTC),
        )


class RetrainingScheduler:
    """Decide if retraining window is due based on elapsed time."""

    def __init__(self, interval_hours: int = 24) -> None:
        self._interval = timedelta(hours=interval_hours)
        self._last_run: datetime | None = None

    def mark_run(self) -> None:
        """Mark scheduler as executed now."""
        self._last_run = datetime.now(tz=UTC)

    @property
    def last_run(self) -> datetime | None:
        """Return last execution timestamp."""
        return self._last_run

    def due(self, now: datetime | None = None) -> bool:
        """Return True when retraining should run."""
        if self._last_run is None:
            return True
        current = now or datetime.now(tz=UTC)
        return current - self._last_run >= self._interval
