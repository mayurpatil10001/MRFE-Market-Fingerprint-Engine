"""Advanced ensemble forecast strategy with regime-aware calibration."""

from __future__ import annotations

import random
from statistics import fmean

from src.core.config.settings import settings
from src.domain.entities.event import Event
from src.domain.entities.fingerprint import Fingerprint
from src.domain.interfaces import ForecastGenerationResult, ForecastGenerator
from src.infrastructure.ml.feature_pipeline import ForecastFeatureVector, MarketFeaturePipeline
from src.infrastructure.ml.forecast_generator_impl import QuantForecastGenerator
from src.infrastructure.ml.similarity_service import FingerprintSimilarityService, mean_float


class AdvancedEnsembleForecastGenerator(ForecastGenerator):
    """Blend baseline quant forecast with regime-aware adjustments."""

    def __init__(
        self,
        baseline_generator: ForecastGenerator | None = None,
        feature_pipeline: MarketFeaturePipeline | None = None,
        similarity_service: FingerprintSimilarityService | None = None,
    ) -> None:
        self._baseline_generator = baseline_generator or QuantForecastGenerator()
        self._feature_pipeline = feature_pipeline or MarketFeaturePipeline()
        self._similarity_service = similarity_service

    async def generate(
        self,
        event: Event,
        fingerprint: Fingerprint,
        asset_symbol: str,
        forecast_horizon_hours: int,
        model_version: str,
    ) -> ForecastGenerationResult:
        """Generate calibrated forecast via ensemble blending."""
        baseline = await self._baseline_generator.generate(
            event=event,
            fingerprint=fingerprint,
            asset_symbol=asset_symbol,
            forecast_horizon_hours=forecast_horizon_hours,
            model_version=model_version,
        )
        features = self._feature_pipeline.build_forecast_features(
            event=event,
            fingerprint=fingerprint,
            forecast_horizon_hours=forecast_horizon_hours,
        )
        regime_signal = self._regime_signal(features=features)
        ensemble_weight = min(0.75, max(0.05, settings.ensemble_regime_weight))
        predicted_movement = round(
            baseline.predicted_movement * (1 - ensemble_weight) + regime_signal * ensemble_weight,
            4,
        )
        confidence_delta = abs(regime_signal - baseline.predicted_movement) * 0.12
        confidence = min(0.99, max(0.1, baseline.confidence - confidence_delta))
        distribution = self._reproject_distribution(
            movement=predicted_movement,
            baseline_distribution=baseline.probability_distribution,
        )
        risk_metrics = dict(baseline.risk_metrics)
        risk_metrics.update(
            {
                "regime_signal": round(regime_signal, 4),
                "ensemble_weight": round(ensemble_weight, 4),
                "model_disagreement": round(abs(regime_signal - baseline.predicted_movement), 4),
            }
        )
        if self._similarity_service is not None:
            similarity = await self._similarity_service.match(
                event=event,
                fingerprint=fingerprint,
                horizon_hours=forecast_horizon_hours,
                asset_symbol=asset_symbol,
                category=str(event.event_type),
                top_k=8,
            )
            if similarity:
                scores = [match.score for match in similarity]
                avg_score = mean_float(scores)
                reaction_values = [
                    float(match.metadata.get("reaction_intensity", "0") or 0.0) for match in similarity
                ]
                avg_reaction = mean_float(reaction_values)
                adjustment = (avg_reaction - fingerprint.reaction_intensity) * 0.25
                direction = 1.0 if (event.sentiment_score or 0.0) >= 0 else -1.0
                predicted_movement = round(max(-1.0, min(1.0, predicted_movement + adjustment * direction)), 4)
                confidence = min(0.99, max(0.1, confidence + avg_score * 0.05))
                distribution = self._reproject_distribution(
                    movement=predicted_movement,
                    baseline_distribution=distribution,
                )
                risk_metrics.update(
                    {
                        "similarity_support": round(avg_score, 4),
                        "similarity_count": float(len(similarity)),
                    }
                )

        intervals = self._monte_carlo_intervals(
            movement=predicted_movement,
            volatility=max(0.02, fingerprint.volatility_impact),
            paths=200,
        )
        risk_metrics.update(intervals)
        return ForecastGenerationResult(
            probability_distribution=distribution,
            predicted_movement=predicted_movement,
            confidence=confidence,
            risk_metrics=risk_metrics,
        )

    @staticmethod
    def _regime_signal(features: ForecastFeatureVector) -> float:
        """Estimate market regime directional signal."""
        weighted = (
            features.sentiment_signal * 0.44
            + features.reaction_intensity * 0.18
            - features.volatility_impact * 0.14
            + features.volume_impact * 0.08
            + features.event_confidence * 0.1
            - features.horizon_factor * 0.07
            - features.sector_risk * 0.09
        )
        return max(-1.0, min(1.0, weighted))

    @staticmethod
    def _reproject_distribution(
        movement: float,
        baseline_distribution: dict[str, float],
    ) -> dict[str, float]:
        """Re-balance distribution around updated movement value."""
        neutral = max(0.08, 1.0 - abs(movement))
        directional = 1.0 - neutral
        positive = directional if movement >= 0 else 0.0
        negative = directional if movement < 0 else 0.0
        candidate = {
            "strong_negative": max(0.0, negative * 0.4 + baseline_distribution.get("strong_negative", 0.0) * 0.4),
            "negative": max(0.0, negative * 0.6 + baseline_distribution.get("negative", 0.0) * 0.4),
            "neutral": max(0.0, neutral * 0.7 + baseline_distribution.get("neutral", 0.0) * 0.3),
            "positive": max(0.0, positive * 0.6 + baseline_distribution.get("positive", 0.0) * 0.4),
            "strong_positive": max(0.0, positive * 0.4 + baseline_distribution.get("strong_positive", 0.0) * 0.4),
        }
        total = sum(candidate.values()) or 1.0
        return {key: round(value / total, 4) for key, value in candidate.items()}

    @staticmethod
    def _monte_carlo_intervals(movement: float, volatility: float, paths: int = 200) -> dict[str, float]:
        """Generate Monte Carlo confidence intervals for the forecast."""
        rng = random.Random(42)
        samples = [movement + rng.gauss(0.0, volatility) for _ in range(max(50, paths))]
        samples.sort()

        def percentile(pct: float) -> float:
            if not samples:
                return 0.0
            index = int((pct / 100.0) * (len(samples) - 1))
            return samples[index]

        interval_50 = (percentile(25), percentile(75))
        interval_90 = (percentile(5), percentile(95))
        interval_95 = (percentile(2.5), percentile(97.5))
        return {
            "mc_paths": float(len(samples)),
            "interval_50_low": round(interval_50[0], 4),
            "interval_50_high": round(interval_50[1], 4),
            "interval_90_low": round(interval_90[0], 4),
            "interval_90_high": round(interval_90[1], 4),
            "interval_95_low": round(interval_95[0], 4),
            "interval_95_high": round(interval_95[1], 4),
            "interval_mean": round(fmean(samples), 4),
        }
