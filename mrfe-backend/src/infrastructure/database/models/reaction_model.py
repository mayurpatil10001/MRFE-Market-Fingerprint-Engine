"""Reaction ORM model."""

from __future__ import annotations

from sqlalchemy import CheckConstraint, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.models.base import (
    Base,
    TimestampMixin,
    VersionMixin,
    generate_uuid,
)


class ReactionModel(Base, TimestampMixin, VersionMixin):
    """Measured market reaction for an event/asset/time horizon."""

    __tablename__ = "reactions"
    __table_args__ = (
        CheckConstraint(
            "reaction_intensity >= 0 AND reaction_intensity <= 1",
            name="ck_reactions_reaction_intensity",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    reaction_id: Mapped[str] = mapped_column(String(36), unique=True, index=True, nullable=False)
    event_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    asset_symbol: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    horizon_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    price_return_pct: Mapped[float] = mapped_column(Float, nullable=False)
    volume_delta_pct: Mapped[float] = mapped_column(Float, nullable=False)
    volatility_delta_pct: Mapped[float] = mapped_column(Float, nullable=False)
    reaction_intensity: Mapped[float] = mapped_column(Float, nullable=False)
    measured_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
