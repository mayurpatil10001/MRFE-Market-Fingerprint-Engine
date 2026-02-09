"""Mapping helpers between domain entities and DTOs."""

from __future__ import annotations

from src.application.dto.responses import (
    EventResponseDTO,
    FingerprintResponseDTO,
    ForecastResponseDTO,
)
from src.domain.entities.event import Event
from src.domain.entities.fingerprint import Fingerprint
from src.domain.entities.forecast import Forecast


def to_event_dto(entity: Event) -> EventResponseDTO:
    """Map Event entity to DTO."""
    return EventResponseDTO(
        event_id=str(entity.event_id),
        event_type=str(entity.event_type),
        severity=str(entity.severity),
        confidence=entity.confidence.value,
        title=entity.title,
        description=entity.description,
        source=entity.source,
        detected_at=entity.detected_at,
        impact_assets=entity.impact_assets,
        market_sector=entity.market_sector,
        country=entity.country,
        sentiment_score=entity.sentiment_score,
        is_active=entity.is_active,
        resolved_at=entity.resolved_at,
        version=entity.version,
    )


def to_fingerprint_dto(entity: Fingerprint) -> FingerprintResponseDTO:
    """Map Fingerprint entity to DTO."""
    return FingerprintResponseDTO(
        fingerprint_id=str(entity.fingerprint_id),
        event_id=str(entity.event_id),
        asset_symbol=entity.asset_symbol,
        reaction_patterns=entity.reaction_patterns,
        baseline_metrics=entity.baseline_metrics,
        reaction_intensity=entity.reaction_intensity,
        duration_minutes=entity.duration_minutes,
        volatility_impact=entity.volatility_impact,
        volume_impact=entity.volume_impact,
        confidence=entity.confidence.value,
        model_version=entity.model_version,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
        version=entity.version,
    )


def to_forecast_dto(entity: Forecast) -> ForecastResponseDTO:
    """Map Forecast entity to DTO."""
    return ForecastResponseDTO(
        forecast_id=str(entity.forecast_id),
        event_id=str(entity.event_id),
        fingerprint_id=str(entity.fingerprint_id),
        asset_symbol=entity.asset_symbol,
        forecast_horizon_hours=entity.forecast_horizon_hours,
        probability_distribution=entity.probability_distribution,
        predicted_movement=entity.predicted_movement,
        confidence=entity.confidence.value,
        risk_metrics=entity.risk_metrics,
        model_version=entity.model_version,
        created_at=entity.created_at,
        expires_at=entity.expires_at,
        version=entity.version,
    )
