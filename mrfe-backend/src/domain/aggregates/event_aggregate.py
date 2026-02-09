"""Aggregate utilities around event relationships."""

from __future__ import annotations

from dataclasses import dataclass, field

from src.domain.entities.event import Event
from src.domain.entities.fingerprint import Fingerprint
from src.domain.entities.forecast import Forecast
from src.domain.exceptions import DomainValidationError


@dataclass(slots=True)
class EventAggregate:
    """Consistency boundary for event, fingerprints, and forecasts."""

    event: Event
    fingerprints: dict[str, Fingerprint] = field(default_factory=dict)
    forecasts: dict[str, Forecast] = field(default_factory=dict)

    def add_fingerprint(self, fingerprint: Fingerprint) -> None:
        """Add one fingerprint per asset symbol."""
        if fingerprint.event_id != self.event.event_id:
            raise DomainValidationError("fingerprint belongs to a different event")
        asset_symbol = fingerprint.asset_symbol.upper()
        if asset_symbol in self.fingerprints:
            raise DomainValidationError("duplicate fingerprint for asset")
        self.fingerprints[asset_symbol] = fingerprint

    def add_forecast(self, forecast: Forecast) -> None:
        """Add one forecast per asset symbol."""
        if forecast.event_id != self.event.event_id:
            raise DomainValidationError("forecast belongs to a different event")
        asset_symbol = forecast.asset_symbol.upper()
        if asset_symbol in self.forecasts:
            raise DomainValidationError("duplicate forecast for asset")
        self.forecasts[asset_symbol] = forecast

    def deactivate(self) -> None:
        """Deactivate aggregate and expire derived forecasts."""
        self.event.deactivate()
        for forecast in self.forecasts.values():
            forecast.expires_at = self.event.resolved_at or forecast.expires_at
