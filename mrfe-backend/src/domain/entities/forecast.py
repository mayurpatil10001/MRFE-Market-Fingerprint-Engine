"""Forecast entity."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Mapping

from src.domain.exceptions import DomainValidationError
from src.domain.value_objects.confidence import Confidence
from src.domain.value_objects.event_id import EventId


@dataclass(slots=True)
class Forecast:
    """Probabilistic forecast generated from event/fingerprint data."""

    forecast_id: EventId
    event_id: EventId
    fingerprint_id: EventId
    asset_symbol: str
    forecast_horizon_hours: int
    probability_distribution: dict[str, float]
    predicted_movement: float
    confidence: Confidence
    risk_metrics: dict[str, float]
    model_version: str
    created_at: datetime
    expires_at: datetime
    version: int = 1

    def __post_init__(self) -> None:
        """Validate forecast invariants."""
        if not self.asset_symbol.strip():
            raise DomainValidationError("asset_symbol must not be empty")
        if self.forecast_horizon_hours <= 0:
            raise DomainValidationError("forecast_horizon_hours must be > 0")
        if self.created_at.tzinfo is None or self.expires_at.tzinfo is None:
            raise DomainValidationError("timestamps must be timezone-aware")
        if self.expires_at <= self.created_at:
            raise DomainValidationError("expires_at must be after created_at")
        if not self.probability_distribution:
            raise DomainValidationError("probability_distribution must not be empty")
        if abs(sum(self.probability_distribution.values()) - 1.0) > 0.01:
            raise DomainValidationError("probability_distribution must sum to 1.0")
        if self.predicted_movement < -1.0 or self.predicted_movement > 1.0:
            raise DomainValidationError("predicted_movement must be in [-1.0, 1.0]")
        if self.version < 1:
            raise DomainValidationError("version must be >= 1")

    @classmethod
    def create(
        cls,
        event_id: EventId,
        fingerprint_id: EventId,
        asset_symbol: str,
        forecast_horizon_hours: int,
        probability_distribution: Mapping[str, float],
        predicted_movement: float,
        confidence: Confidence,
        risk_metrics: Mapping[str, float],
        model_version: str,
    ) -> "Forecast":
        """Create a forecast with expiration derived from horizon."""
        now = datetime.now(tz=timezone.utc)
        return cls(
            forecast_id=EventId.new(),
            event_id=event_id,
            fingerprint_id=fingerprint_id,
            asset_symbol=asset_symbol.upper(),
            forecast_horizon_hours=forecast_horizon_hours,
            probability_distribution=dict(probability_distribution),
            predicted_movement=predicted_movement,
            confidence=confidence,
            risk_metrics=dict(risk_metrics),
            model_version=model_version,
            created_at=now,
            expires_at=now + timedelta(hours=forecast_horizon_hours),
        )

    def is_expired(self) -> bool:
        """Return whether forecast expired."""
        return datetime.now(tz=timezone.utc) > self.expires_at
