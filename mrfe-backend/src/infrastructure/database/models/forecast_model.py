"""SQLAlchemy forecast model."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from src.infrastructure.database.models.base import (
    Base,
    TimestampMixin,
    VersionMixin,
    generate_uuid,
)


class ForecastModel(Base, TimestampMixin, VersionMixin):
    """Persistence model for domain Forecast."""

    __tablename__ = "forecasts"
    __table_args__ = (
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_forecasts_confidence"),
        CheckConstraint(
            "predicted_movement >= -1 AND predicted_movement <= 1",
            name="ck_forecasts_predicted_movement",
        ),
        Index("ix_forecasts_event_asset", "event_id", "asset_symbol"),
        Index("ix_forecasts_expires_at", "expires_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    forecast_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True, index=True)
    event_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("events.event_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    fingerprint_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("fingerprints.fingerprint_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    asset_symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    forecast_horizon_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    probability_distribution: Mapped[dict[str, float]] = mapped_column(
        JSON,
        nullable=False,
    )
    predicted_movement: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    risk_metrics: Mapped[dict[str, float]] = mapped_column(
        JSON,
        nullable=False,
    )
    model_version: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
