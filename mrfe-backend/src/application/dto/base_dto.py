"""Base DTO and response envelope models."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class StrictBaseModel(BaseModel):
    """Base model with strict enterprise defaults."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
        protected_namespaces=(),
    )


class ResultEnvelope(StrictBaseModel, Generic[T]):
    """Generic API-safe response envelope."""

    success: bool = Field(default=True)
    data: T | None = None
    error_code: str | None = None
    error_message: str | None = None

    @classmethod
    def ok(cls, data: T) -> "ResultEnvelope[T]":
        """Construct successful result."""
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, error_code: str, error_message: str) -> "ResultEnvelope[T]":
        """Construct failed result."""
        return cls(success=False, error_code=error_code, error_message=error_message)
