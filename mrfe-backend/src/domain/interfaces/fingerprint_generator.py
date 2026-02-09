"""Port for fingerprint generation strategies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from src.domain.entities.event import Event


@dataclass(frozen=True, slots=True)
class FingerprintGenerationResult:
    """Result payload used to build fingerprint entity."""

    reaction_patterns: dict[str, float]
    baseline_metrics: dict[str, float]
    reaction_intensity: float
    duration_minutes: int
    volatility_impact: float
    volume_impact: float
    confidence: float


class FingerprintGenerator(Protocol):
    """Port for interchangeable fingerprint-generation algorithms."""

    async def generate(
        self,
        event: Event,
        asset_symbol: str,
        model_version: str,
    ) -> FingerprintGenerationResult:
        """Generate deterministic output used to create fingerprint aggregate."""
