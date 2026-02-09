"""Fingerprint generation strategy implementations."""

from __future__ import annotations

import asyncio
import hashlib
from typing import Any

from src.domain.entities.event import Event
from src.domain.interfaces import FingerprintGenerationResult, FingerprintGenerator
from src.core.config.settings import settings
from src.infrastructure.ml.model_loader import get_model_loader


class DeterministicFingerprintGenerator(FingerprintGenerator):
    """Deterministic fingerprint strategy for production-safe baseline."""

    async def generate(
        self,
        event: Event,
        asset_symbol: str,
        model_version: str,
    ) -> FingerprintGenerationResult:
        """Generate fingerprint values deterministically."""
        seed = int(hashlib.sha256(f"{event.event_id}:{asset_symbol}".encode()).hexdigest()[:8], 16)
        normalized = seed / 0xFFFFFFFF
        reaction_intensity = min(0.95, max(0.1, event.confidence.value * (0.5 + normalized / 2)))
        return FingerprintGenerationResult(
            reaction_patterns={
                "initial_shock": round(reaction_intensity, 4),
                "reversion_speed": round(0.2 + normalized * 0.6, 4),
            },
            baseline_metrics={
                "avg_volatility": round(0.02 + normalized * 0.03, 4),
                "avg_volume_index": round(1.0 + normalized, 4),
            },
            reaction_intensity=round(reaction_intensity, 4),
            duration_minutes=int(120 + normalized * 720),
            volatility_impact=round(0.05 + normalized * 0.3, 4),
            volume_impact=round(0.10 + normalized * 1.5, 4),
            confidence=min(0.99, round(event.confidence.value * 0.95 + 0.02, 4)),
        )


class MLFingerprintGenerator(FingerprintGenerator):
    """ML-based fingerprint generator with deterministic fallback."""

    _severity_weight = {
        "LOW": 0.2,
        "MEDIUM": 0.5,
        "HIGH": 0.8,
        "CRITICAL": 1.0,
    }

    def __init__(self, fallback: FingerprintGenerator | None = None) -> None:
        self._fallback = fallback or DeterministicFingerprintGenerator()
        self._model_loader = get_model_loader()

    async def generate(
        self,
        event: Event,
        asset_symbol: str,
        model_version: str,
    ) -> FingerprintGenerationResult:
        """Generate fingerprint values using a regressor when available."""
        model = await self._model_loader.load_sklearn_model(settings.fingerprint_regressor_path)
        if model is None:
            return await self._fallback.generate(
                event=event,
                asset_symbol=asset_symbol,
                model_version=model_version,
            )
        features = self._features(event=event)
        prediction = await self._predict(model=model, features=features)
        if prediction is None:
            return await self._fallback.generate(
                event=event,
                asset_symbol=asset_symbol,
                model_version=model_version,
            )
        reaction_intensity = min(0.99, max(0.05, prediction))
        volatility_impact = min(1.0, max(0.05, reaction_intensity * 0.55 + 0.08))
        volume_impact = min(1.5, max(0.1, reaction_intensity * 1.2 + 0.15))
        duration_minutes = int(90 + reaction_intensity * 600)
        return FingerprintGenerationResult(
            reaction_patterns={
                "initial_shock": round(reaction_intensity, 4),
                "reversion_speed": round(0.25 + reaction_intensity * 0.5, 4),
                "secondary_aftershock": round(reaction_intensity * 0.35, 4),
            },
            baseline_metrics={
                "avg_volatility": round(0.02 + volatility_impact * 0.04, 4),
                "avg_volume_index": round(1.0 + volume_impact, 4),
            },
            reaction_intensity=round(reaction_intensity, 4),
            duration_minutes=duration_minutes,
            volatility_impact=round(volatility_impact, 4),
            volume_impact=round(volume_impact, 4),
            confidence=min(0.99, round(event.confidence.value * 0.9 + 0.08, 4)),
        )

    def _features(self, event: Event) -> list[float]:
        severity = self._severity_weight.get(str(event.severity).upper(), 0.5)
        sentiment = float(event.sentiment_score or 0.0)
        confidence = float(event.confidence.value)
        return [confidence, sentiment, severity]

    async def _predict(self, model: Any, features: list[float]) -> float | None:
        try:
            result = await asyncio.to_thread(model.predict, [features])
        except Exception:  # noqa: BLE001
            return None
        try:
            value = float(result[0])
        except (TypeError, ValueError, IndexError):
            return None
        return value
