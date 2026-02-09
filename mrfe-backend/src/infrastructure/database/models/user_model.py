"""User ORM model."""

from __future__ import annotations

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.models.base import (
    Base,
    TimestampMixin,
    VersionMixin,
    generate_uuid,
)


class UserModel(Base, TimestampMixin, VersionMixin):
    """Application user record used for auth/account state."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    roles_csv: Mapped[str] = mapped_column(String(255), nullable=False, default="reader")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
