"""Structured logging bootstrap."""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog

from src.core.config.settings import settings
from src.core.logging.processors import mask_sensitive_data


def configure_logging() -> None:
    """Configure stdlib + structlog JSON logging."""
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            mask_sensitive_data,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> Any:
    """Get structured logger."""
    return structlog.get_logger(name)
