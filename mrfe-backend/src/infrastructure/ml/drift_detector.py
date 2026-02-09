"""Model drift detection primitives for online monitoring."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DriftReport:
    """Drift evaluation result."""

    drift_score: float
    status: str
    baseline_entropy: float
    live_entropy: float


class PopulationDriftDetector:
    """Detect drift using Jensen-Shannon divergence on probability vectors."""

    def evaluate(
        self,
        baseline_distribution: dict[str, float],
        live_distribution: dict[str, float],
        alert_threshold: float,
    ) -> DriftReport:
        """Evaluate distribution drift and classify status."""
        keys = sorted(set(baseline_distribution).union(live_distribution))
        baseline = self._normalize([baseline_distribution.get(key, 0.0) for key in keys])
        live = self._normalize([live_distribution.get(key, 0.0) for key in keys])
        midpoint = [(left + right) / 2 for left, right in zip(baseline, live, strict=True)]
        jsd = (self._kl_divergence(baseline, midpoint) + self._kl_divergence(live, midpoint)) / 2
        drift_score = round(math.sqrt(jsd), 6)
        if drift_score >= alert_threshold:
            status = "drift_alert"
        elif drift_score >= alert_threshold * 0.65:
            status = "watch"
        else:
            status = "stable"
        return DriftReport(
            drift_score=drift_score,
            status=status,
            baseline_entropy=round(self._entropy(baseline), 6),
            live_entropy=round(self._entropy(live), 6),
        )

    @staticmethod
    def _normalize(values: list[float]) -> list[float]:
        cleaned = [max(0.0, value) for value in values]
        total = sum(cleaned)
        if total <= 0:
            return [1.0 / len(cleaned)] * len(cleaned)
        return [value / total for value in cleaned]

    @staticmethod
    def _entropy(values: list[float]) -> float:
        return -sum(value * math.log(value) for value in values if value > 0)

    @staticmethod
    def _kl_divergence(left: list[float], right: list[float]) -> float:
        epsilon = 1e-12
        return sum(
            left_value * math.log((left_value + epsilon) / (right_value + epsilon))
            for left_value, right_value in zip(left, right, strict=True)
            if left_value > 0
        )
