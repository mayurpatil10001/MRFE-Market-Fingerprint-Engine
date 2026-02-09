"""SQLAlchemy fingerprint model."""

from __future__ import annotations

from sqlalchemy import CheckConstraint, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from src.infrastructure.database.models.base import (
    Base,
    TimestampMixin,
    VersionMixin,
    generate_uuid,
)


class FingerprintModel(Base, TimestampMixin, VersionMixin):
    """Persistence model for domain Fingerprint."""

    __tablename__ = "fingerprints"
    __table_args__ = (
        CheckConstraint(
            "reaction_intensity >= 0 AND reaction_intensity <= 1",
            name="ck_fingerprints_reaction_intensity",
        ),
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_fingerprints_confidence"),
        Index("ix_fingerprints_event_asset", "event_id", "asset_symbol", unique=True),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    fingerprint_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True, index=True)
    event_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("events.event_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    asset_symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    reaction_patterns: Mapped[dict[str, float]] = mapped_column(
        JSON,
        nullable=False,
    )
    baseline_metrics: Mapped[dict[str, float]] = mapped_column(
        JSON,
        nullable=False,
    )
    reaction_intensity: Mapped[float] = mapped_column(Float, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    volatility_impact: Mapped[float] = mapped_column(Float, nullable=False)
    volume_impact: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    model_version: Mapped[str] = mapped_column(String(32), nullable=False)
