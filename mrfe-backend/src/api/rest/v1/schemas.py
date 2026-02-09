"""API v1 request/response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


class APIModel(BaseModel):
    """Strict API base model."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, protected_namespaces=())


class NewsDetectionRequest(APIModel):
    """Event detection request payload."""

    news_content: Annotated[str, Field(min_length=20, max_length=30000)]
    source: Annotated[str, Field(min_length=3, max_length=120)]


class EventClassificationRequest(APIModel):
    """Event classification request payload."""

    title: Annotated[str, Field(min_length=3, max_length=255)]
    description: Annotated[str, Field(min_length=20, max_length=30000)]
    source: Annotated[str, Field(min_length=3, max_length=120)] = "manual"


class GenerateFingerprintRequest(APIModel):
    """Fingerprint generation request payload."""

    event_id: str
    asset_symbol: Annotated[str, Field(min_length=1, max_length=20)]
    model_version: str = "v1"


class UpdateFingerprintRequest(APIModel):
    """Fingerprint update request payload."""

    reaction_intensity: Annotated[float | None, Field(ge=0.0, le=1.0)] = None
    volatility_impact: float | None = None
    volume_impact: float | None = None


class GenerateForecastRequest(APIModel):
    """Forecast generation request payload."""

    event_id: str
    fingerprint_id: str
    asset_symbol: Annotated[str, Field(min_length=1, max_length=20)]
    forecast_horizon_hours: Annotated[int, Field(ge=1, le=240)] = 24
    model_version: str = "v1"


class TokenRequest(APIModel):
    """Token issue request."""

    user_id: str
    roles: list[str] = ["reader"]


class RefreshTokenRequest(APIModel):
    """Refresh token request."""

    refresh_token: str
    roles: list[str] = ["reader"]


class TokenResponse(APIModel):
    """Token response payload."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class EventResponse(APIModel):
    """Event response payload."""

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


class FingerprintResponse(APIModel):
    """Fingerprint response payload."""

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


class ForecastResponse(APIModel):
    """Forecast response payload."""

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


class ForecastBacktestRequest(APIModel):
    """Backtest request payload."""

    predictions: Annotated[list[float], Field(min_length=5, max_length=5000)]
    actuals: Annotated[list[float], Field(min_length=5, max_length=5000)]


class ForecastBacktestResponse(APIModel):
    """Backtest result payload."""

    mae: float
    rmse: float
    directional_accuracy: float


class SearchEventsResponse(APIModel):
    """Paginated event search response."""

    items: list[EventResponse]
    page: int
    page_size: int
    total: int


class SearchFingerprintsResponse(APIModel):
    """Paginated fingerprint search response."""

    items: list[FingerprintResponse]
    page: int
    page_size: int
    total: int


class SearchForecastsResponse(APIModel):
    """Paginated forecast search response."""

    items: list[ForecastResponse]
    page: int
    page_size: int
    total: int


class NewsItemResponse(APIModel):
    """Stored news article payload."""

    article_id: str
    source: str
    title: str
    summary: str
    url: str
    published_at: datetime
    author: str | None = None


class SearchNewsResponse(APIModel):
    """Paginated news response."""

    items: list[NewsItemResponse]
    page: int
    page_size: int
    total: int


class MeasureReactionRequest(APIModel):
    """Reaction measurement request payload."""

    event_id: str
    asset_symbol: Annotated[str, Field(min_length=1, max_length=20)]
    pre_event_price: float
    post_event_price: float
    pre_event_volume: Annotated[float, Field(gt=0)]
    post_event_volume: Annotated[float, Field(gt=0)]
    pre_event_volatility: Annotated[float, Field(ge=0)]
    post_event_volatility: Annotated[float, Field(ge=0)]
    horizon_minutes: Annotated[int, Field(ge=1, le=43200)] = 60


class MeasureReactionResponse(APIModel):
    """Reaction measurement response payload."""

    event_id: str
    asset_symbol: str
    horizon_minutes: int
    price_return_pct: float
    volume_delta_pct: float
    volatility_delta_pct: float
    reaction_intensity: Annotated[float, Field(ge=0.0, le=1.0)]
    measured_at: datetime


class ReactionObservationInput(APIModel):
    """One market observation around an event."""

    timestamp: datetime
    price: float
    volume: float
    spread_bps: float | None = None


class ReactionAnalysisRequest(APIModel):
    """Reaction analysis request payload."""

    event_id: str
    asset_symbol: Annotated[str, Field(min_length=1, max_length=20)]
    event_time: datetime
    observations: Annotated[list[ReactionObservationInput], Field(min_length=6, max_length=20000)]
    horizons_minutes: list[int] | None = None


class ReactionHorizonResponse(APIModel):
    """Reaction measurement for one horizon."""

    horizon_minutes: int
    price_return_pct: float
    volume_delta_pct: float
    volatility_delta_pct: float
    spread_delta_bps: float | None
    reaction_intensity: Annotated[float, Field(ge=0.0, le=1.0)]


class ReactionAnalysisResponse(APIModel):
    """Reaction analysis response payload."""

    event_id: str
    asset_symbol: str
    measured_at: datetime
    baseline_price: float
    baseline_volume: float
    baseline_volatility: float
    horizons: list[ReactionHorizonResponse]
    quality: dict[str, float | int]


class GenerateIntelRequest(APIModel):
    """AI intelligence generation payload."""

    symbol: Annotated[str, Field(min_length=1, max_length=20)]
    market_context: Annotated[str, Field(min_length=20, max_length=6000)]
    horizon_hours: Annotated[int, Field(ge=1, le=168)] = 24
    risk_profile: Literal["conservative", "balanced", "aggressive"] = "balanced"
    provider: Literal["openrouter", "anthropic", "heuristic"] | None = None
    model: Annotated[str | None, Field(max_length=80)] = None


class IntelScenario(APIModel):
    """One probabilistic market scenario."""

    name: Annotated[str, Field(min_length=2, max_length=80)]
    probability: Annotated[float, Field(ge=0.0, le=1.0)]
    expected_move_percent: float
    confidence: Annotated[float, Field(ge=0.0, le=1.0)]
    rationale: Annotated[str, Field(min_length=4, max_length=500)]


class IntelResponse(APIModel):
    """Generated AI intelligence response."""

    provider: str
    model: str | None = None
    generated_at: datetime
    symbol: str
    summary: str
    key_drivers: list[str]
    action_bias: Literal["bullish", "bearish", "neutral"]
    scenarios: list[IntelScenario]
    warnings: list[str] = []


class ModelRegistrationRequest(APIModel):
    """Model registry registration payload."""

    name: Annotated[str, Field(min_length=2, max_length=80)]
    version: Annotated[str, Field(min_length=1, max_length=40)]
    framework: Annotated[str, Field(min_length=2, max_length=40)]
    artifact_uri: Annotated[str, Field(min_length=8, max_length=500)]
    tags: dict[str, str] = {}


class ModelRecordResponse(APIModel):
    """Model registry metadata response."""

    model_id: str
    name: str
    version: str
    framework: str
    artifact_uri: str
    stage: str
    created_at: str
    tags: dict[str, str]


class PromoteModelRequest(APIModel):
    """Model stage transition payload."""

    stage: Literal["production", "canary", "shadow"] = "production"


class DriftCheckRequest(APIModel):
    """Distribution drift check payload."""

    model_version: Annotated[str, Field(min_length=1, max_length=40)]
    baseline_distribution: dict[str, float]
    live_distribution: dict[str, float]


class DriftCheckResponse(APIModel):
    """Drift analysis response."""

    drift_score: float
    status: str
    threshold: float
    retrain_queued: bool
    task_id: str | None = None
    baseline_entropy: float
    live_entropy: float


class IncrementalUpdateRequest(APIModel):
    """Incremental learner update payload."""

    vector: list[float]


class IncrementalUpdateResponse(APIModel):
    """Incremental learner update response."""

    observations: int
    centroid: list[float]
    updated_at: datetime | None = None


class RegimeDetectRequest(APIModel):
    """Regime detection payload."""

    returns: list[float]


class RegimeDetectResponse(APIModel):
    """Regime detection response."""

    regime: str
    volatility_score: float
    trend_score: float
    detected_at: datetime


class RetrainingScheduleResponse(APIModel):
    """Retraining scheduler status."""

    due: bool
    interval_hours: int
    last_run: datetime | None = None
