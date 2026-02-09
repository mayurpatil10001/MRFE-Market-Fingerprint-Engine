"""Add reactions and users tables.

Revision ID: 0002_reactions_and_users
Revises: 0001_initial_schema
Create Date: 2026-02-08
"""

from __future__ import annotations

from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision = "0002_reactions_and_users"
down_revision = "0001_initial_schema"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    """Create reactions and users tables."""
    op.create_table(
        "reactions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("reaction_id", sa.String(length=36), nullable=False),
        sa.Column("event_id", sa.String(length=36), nullable=False),
        sa.Column("asset_symbol", sa.String(length=20), nullable=False),
        sa.Column("horizon_minutes", sa.Integer(), nullable=False),
        sa.Column("price_return_pct", sa.Float(), nullable=False),
        sa.Column("volume_delta_pct", sa.Float(), nullable=False),
        sa.Column("volatility_delta_pct", sa.Float(), nullable=False),
        sa.Column("reaction_intensity", sa.Float(), nullable=False),
        sa.Column("measured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.CheckConstraint(
            "reaction_intensity >= 0 AND reaction_intensity <= 1",
            name="ck_reactions_reaction_intensity",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("reaction_id"),
    )
    op.create_index("ix_reactions_reaction_id", "reactions", ["reaction_id"], unique=True)
    op.create_index("ix_reactions_event_id", "reactions", ["event_id"], unique=False)
    op.create_index("ix_reactions_asset_symbol", "reactions", ["asset_symbol"], unique=False)

    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("roles_csv", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_users_user_id", "users", ["user_id"], unique=True)


def downgrade() -> None:
    """Drop reactions and users tables."""
    op.drop_table("users")
    op.drop_table("reactions")
