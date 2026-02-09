"""Initial MRFE schema.

Revision ID: 0001_initial_schema
Revises: None
Create Date: 2026-02-07
"""

from __future__ import annotations

from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision = "0001_initial_schema"
down_revision = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    """Create initial tables and indexes."""
    op.create_table(
        "events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("event_id", sa.String(length=36), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=24), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("source", sa.String(length=128), nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("impact_assets", sa.JSON(), nullable=False),
        sa.Column("market_sector", sa.String(length=64), nullable=True),
        sa.Column("country", sa.String(length=64), nullable=True),
        sa.Column("sentiment_score", sa.Float(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_events_confidence"),
        sa.CheckConstraint(
            "sentiment_score IS NULL OR (sentiment_score >= -1 AND sentiment_score <= 1)",
            name="ck_events_sentiment",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id"),
    )
    op.create_index("ix_events_event_id", "events", ["event_id"], unique=True)
    op.create_index("ix_events_event_type", "events", ["event_type"], unique=False)
    op.create_index("ix_events_source", "events", ["source"], unique=False)
    op.create_index("ix_events_severity", "events", ["severity"], unique=False)
    op.create_index("ix_events_is_active", "events", ["is_active"], unique=False)

    op.create_table(
        "fingerprints",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("fingerprint_id", sa.String(length=36), nullable=False),
        sa.Column("event_id", sa.String(length=36), nullable=False),
        sa.Column("asset_symbol", sa.String(length=20), nullable=False),
        sa.Column("reaction_patterns", sa.JSON(), nullable=False),
        sa.Column("baseline_metrics", sa.JSON(), nullable=False),
        sa.Column("reaction_intensity", sa.Float(), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("volatility_impact", sa.Float(), nullable=False),
        sa.Column("volume_impact", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("model_version", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.CheckConstraint(
            "reaction_intensity >= 0 AND reaction_intensity <= 1",
            name="ck_fingerprints_reaction_intensity",
        ),
        sa.CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_fingerprints_confidence"),
        sa.ForeignKeyConstraint(["event_id"], ["events.event_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("fingerprint_id"),
    )
    op.create_index("ix_fingerprints_fingerprint_id", "fingerprints", ["fingerprint_id"], unique=True)
    op.create_index("ix_fingerprints_event_id", "fingerprints", ["event_id"], unique=False)
    op.create_index("ix_fingerprints_asset_symbol", "fingerprints", ["asset_symbol"], unique=False)
    op.create_index(
        "ix_fingerprints_event_asset",
        "fingerprints",
        ["event_id", "asset_symbol"],
        unique=True,
    )

    op.create_table(
        "forecasts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("forecast_id", sa.String(length=36), nullable=False),
        sa.Column("event_id", sa.String(length=36), nullable=False),
        sa.Column("fingerprint_id", sa.String(length=36), nullable=False),
        sa.Column("asset_symbol", sa.String(length=20), nullable=False),
        sa.Column("forecast_horizon_hours", sa.Integer(), nullable=False),
        sa.Column("probability_distribution", sa.JSON(), nullable=False),
        sa.Column("predicted_movement", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("risk_metrics", sa.JSON(), nullable=False),
        sa.Column("model_version", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_forecasts_confidence"),
        sa.CheckConstraint(
            "predicted_movement >= -1 AND predicted_movement <= 1",
            name="ck_forecasts_predicted_movement",
        ),
        sa.ForeignKeyConstraint(["event_id"], ["events.event_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["fingerprint_id"], ["fingerprints.fingerprint_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("forecast_id"),
    )
    op.create_index("ix_forecasts_forecast_id", "forecasts", ["forecast_id"], unique=True)
    op.create_index("ix_forecasts_event_id", "forecasts", ["event_id"], unique=False)
    op.create_index("ix_forecasts_fingerprint_id", "forecasts", ["fingerprint_id"], unique=False)
    op.create_index("ix_forecasts_asset_symbol", "forecasts", ["asset_symbol"], unique=False)
    op.create_index("ix_forecasts_expires_at", "forecasts", ["expires_at"], unique=False)


def downgrade() -> None:
    """Drop all schema objects."""
    op.drop_table("forecasts")
    op.drop_table("fingerprints")
    op.drop_table("events")
