"""Use-case response DTOs."""

from __future__ import annotations

from datetime import datetime

from src.application.dto.base_dto import StrictBaseModel


class EventResponseDTO(StrictBaseModel):
    """Event read model."""

    event_id: str
    event_type: str
    severity: str
    confidence: float
    title: str
    description: str
    source: str
    detected_at: datetime
    impact_assets: tuple[str, ...]
    market_sector: str | None = None
    country: str | None = None
    sentiment_score: float | None = None
    is_active: bool
    resolved_at: datetime | None = None
    version: int


class FingerprintResponseDTO(StrictBaseModel):
    """Fingerprint read model."""

    fingerprint_id: str
    event_id: str
    asset_symbol: str
    reaction_patterns: dict[str, float]
    baseline_metrics: dict[str, float]
    reaction_intensity: float
    duration_minutes: int
    volatility_impact: float
    volume_impact: float
    confidence: float
    model_version: str
    created_at: datetime
    updated_at: datetime
    version: int


class ForecastResponseDTO(StrictBaseModel):
    """Forecast read model."""

    forecast_id: str
    event_id: str
    fingerprint_id: str
    asset_symbol: str
    forecast_horizon_hours: int
    probability_distribution: dict[str, float]
    predicted_movement: float
    confidence: float
    risk_metrics: dict[str, float]
    model_version: str
    created_at: datetime
    expires_at: datetime
    version: int


class SearchEventsResponseDTO(StrictBaseModel):
    """Paginated event search payload."""

    items: list[EventResponseDTO]
    page: int
    page_size: int
    total: int
