"""Environment presets."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EnvironmentPreset:
    """Runtime preset values."""

    name: str
    debug: bool
    database_echo: bool
    rate_limit_per_minute: int


DEVELOPMENT = EnvironmentPreset(name="development", debug=True, database_echo=True, rate_limit_per_minute=600)
STAGING = EnvironmentPreset(name="staging", debug=False, database_echo=False, rate_limit_per_minute=240)
PRODUCTION = EnvironmentPreset(name="production", debug=False, database_echo=False, rate_limit_per_minute=120)
