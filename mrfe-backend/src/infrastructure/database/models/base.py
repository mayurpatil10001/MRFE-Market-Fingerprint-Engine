"""SQLAlchemy model base."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def generate_uuid() -> str:
    """Generate UUID string for keys."""
    return str(uuid4())


class Base(DeclarativeBase):
    """Declarative base class."""


class TimestampMixin:
    """Adds created_at and updated_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(tz=timezone.utc),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(tz=timezone.utc),
        onupdate=func.now(),
        server_default=func.now(),
    )


class VersionMixin:
    """Adds integer optimistic lock version."""

    version: Mapped[int] = mapped_column(nullable=False, default=1)
