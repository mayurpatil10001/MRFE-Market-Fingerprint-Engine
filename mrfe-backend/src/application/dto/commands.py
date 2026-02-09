"""CQRS command DTOs."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field, field_validator

from src.application.dto.base_dto import StrictBaseModel


class DetectEventFromNewsCommand(StrictBaseModel):
    """Command for event detection from text news."""

    news_content: Annotated[str, Field(min_length=20, max_length=30000)]
    source: Annotated[str, Field(min_length=3, max_length=120)]


class GenerateFingerprintCommand(StrictBaseModel):
    """Command for fingerprint generation."""

    event_id: str
    asset_symbol: Annotated[str, Field(min_length=1, max_length=20)]
    model_version: Annotated[str, Field(min_length=1, max_length=32)] = "v1"

    @field_validator("asset_symbol")
    @classmethod
    def validate_asset_symbol(cls, value: str) -> str:
        """Normalize asset symbol."""
        return value.upper()


class UpdateFingerprintCommand(StrictBaseModel):
    """Command for fingerprint mutation."""

    fingerprint_id: str
    reaction_intensity: Annotated[float | None, Field(ge=0.0, le=1.0)] = None
    volatility_impact: float | None = None
    volume_impact: float | None = None


class GenerateForecastCommand(StrictBaseModel):
    """Command for forecast generation."""

    event_id: str
    fingerprint_id: str
    asset_symbol: Annotated[str, Field(min_length=1, max_length=20)]
    forecast_horizon_hours: Annotated[int, Field(ge=1, le=240)] = 24
    model_version: Annotated[str, Field(min_length=1, max_length=32)] = "v1"

    @field_validator("asset_symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        """Normalize symbol."""
        return value.upper()
