"""Structlog processors."""

from __future__ import annotations

from structlog.typing import EventDict, WrappedLogger

SENSITIVE_KEYS = {
    "password",
    "secret",
    "token",
    "api_key",
    "private_key",
    "authorization",
    "refresh_token",
}


def mask_sensitive_data(_: WrappedLogger, __: str, event_dict: EventDict) -> EventDict:
    """Mask sensitive values in structured logs."""
    for key in list(event_dict.keys()):
        if key.lower() in SENSITIVE_KEYS:
            event_dict[key] = "***"
    return event_dict
