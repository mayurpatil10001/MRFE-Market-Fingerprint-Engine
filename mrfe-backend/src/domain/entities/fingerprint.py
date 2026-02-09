"""Fingerprint entity."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Mapping

from src.domain.exceptions import DomainValidationError
from src.domain.value_objects.confidence import Confidence
from src.domain.value_objects.event_id import EventId


@dataclass(slots=True)
class Fingerprint:
    """Behavioral fingerprint entity for event/asset reaction."""

    fingerprint_id: EventId
    event_id: EventId
    asset_symbol: str
    reaction_patterns: dict[str, float]
    baseline_metrics: dict[str, float]
    reaction_intensity: float
    duration_minutes: int
    volatility_impact: float
    volume_impact: float
    confidence: Confidence
    model_version: str
    created_at: datetime
    updated_at: datetime
    version: int = 1

    def __post_init__(self) -> None:
        """Validate fingerprint invariants."""
        if not self.asset_symbol.strip():
            raise DomainValidationError("asset_symbol must not be empty")
        if self.reaction_intensity < 0.0 or self.reaction_intensity > 1.0:
            raise DomainValidationError("reaction_intensity must be between 0 and 1")
        if self.duration_minutes <= 0:
            raise DomainValidationError("duration_minutes must be > 0")
        if self.created_at.tzinfo is None or self.updated_at.tzinfo is None:
            raise DomainValidationError("timestamps must be timezone-aware")
        if self.updated_at < self.created_at:
            raise DomainValidationError("updated_at cannot be earlier than created_at")
        if self.version < 1:
            raise DomainValidationError("version must be >= 1")

    @classmethod
    def create(
        cls,
        event_id: EventId,
        asset_symbol: str,
        reaction_patterns: Mapping[str, float],
        baseline_metrics: Mapping[str, float],
        reaction_intensity: float,
        duration_minutes: int,
        volatility_impact: float,
        volume_impact: float,
        confidence: Confidence,
        model_version: str,
    ) -> "Fingerprint":
        """Create a new fingerprint instance."""
        now = datetime.now(tz=timezone.utc)
        return cls(
            fingerprint_id=EventId.new(),
            event_id=event_id,
            asset_symbol=asset_symbol.upper(),
            reaction_patterns=dict(reaction_patterns),
            baseline_metrics=dict(baseline_metrics),
            reaction_intensity=reaction_intensity,
            duration_minutes=duration_minutes,
            volatility_impact=volatility_impact,
            volume_impact=volume_impact,
            confidence=confidence,
            model_version=model_version,
            created_at=now,
            updated_at=now,
        )

    def update(
        self,
        reaction_intensity: float | None = None,
        volatility_impact: float | None = None,
        volume_impact: float | None = None,
    ) -> None:
        """Update mutable fingerprint attributes."""
        if reaction_intensity is not None:
            if reaction_intensity < 0.0 or reaction_intensity > 1.0:
                raise DomainValidationError("reaction_intensity must be between 0 and 1")
            self.reaction_intensity = reaction_intensity
        if volatility_impact is not None:
            self.volatility_impact = volatility_impact
        if volume_impact is not None:
            self.volume_impact = volume_impact
        self.updated_at = datetime.now(tz=timezone.utc)
        self.version += 1
