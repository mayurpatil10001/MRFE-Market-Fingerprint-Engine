"""FastAPI exception mapping."""

from __future__ import annotations

from typing import cast

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from src.core.config.settings import settings
from src.core.logging import get_logger
from src.domain.exceptions import (
    ConcurrencyConflictError,
    DomainError,
    DomainNotFoundError,
    DomainValidationError,
    DuplicateEntityError,
)

logger = get_logger(__name__)


async def domain_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    """Map domain exceptions to HTTP status codes."""
    domain_exc = cast(DomainError, exc)
    if isinstance(domain_exc, DomainNotFoundError):
        status_code = 404
    elif isinstance(domain_exc, DomainValidationError):
        status_code = 400
    elif isinstance(domain_exc, DuplicateEntityError):
        status_code = 409
    elif isinstance(domain_exc, ConcurrencyConflictError):
        status_code = 409
    else:
        status_code = 500
    logger.error("domain_exception", error=str(domain_exc), error_type=domain_exc.__class__.__name__)
    return JSONResponse(
        status_code=status_code,
        content={"error_code": domain_exc.__class__.__name__, "detail": str(domain_exc)},
    )


async def validation_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    """Map pydantic validation exceptions."""
    validation_exc = cast(ValidationError, exc)
    return JSONResponse(status_code=422, content={"detail": validation_exc.errors()})


async def integrity_error_handler(_: Request, exc: Exception) -> JSONResponse:
    """Map SQL integrity errors."""
    integrity_exc = cast(IntegrityError, exc)
    logger.error("integrity_error", error=str(integrity_exc))
    return JSONResponse(
        status_code=409,
        content={"error_code": "INTEGRITY_ERROR", "detail": "database integrity violation"},
    )


async def fallback_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    """Fallback exception handler."""
    logger.exception("unhandled_exception", error=str(exc))
    detail = "internal server error" if settings.is_production else str(exc)
    return JSONResponse(status_code=500, content={"error_code": "INTERNAL_ERROR", "detail": detail})


def register_exception_handlers(app: FastAPI) -> None:
    """Register application exception handlers."""
    app.add_exception_handler(DomainError, domain_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)
    app.add_exception_handler(IntegrityError, integrity_error_handler)
    app.add_exception_handler(Exception, fallback_exception_handler)
