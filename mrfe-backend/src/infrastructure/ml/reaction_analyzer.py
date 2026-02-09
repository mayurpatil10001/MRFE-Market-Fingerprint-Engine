"""Reaction analysis utilities for event impact measurement across horizons."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from statistics import fmean


@dataclass(frozen=True, slots=True)
class ReactionObservation:
    """One normalized market observation around an event."""

    timestamp: datetime
    price: float
    volume: float
    spread_bps: float | None = None


@dataclass(frozen=True, slots=True)
class HorizonReaction:
    """Reaction measurement for one horizon."""

    horizon_minutes: int
    price_return_pct: float
    volume_delta_pct: float
    volatility_delta_pct: float
    spread_delta_bps: float | None
    reaction_intensity: float


@dataclass(frozen=True, slots=True)
class ReactionAnalysisResult:
    """Reaction analysis payload for one event/asset."""

    event_id: str
    asset_symbol: str
    measured_at: datetime
    baseline_price: float
    baseline_volume: float
    baseline_volatility: float
    horizons: tuple[HorizonReaction, ...]
    quality: dict[str, float | int]


class ReactionAnalyzer:
    """Compute multi-horizon reaction metrics with basic data-quality controls."""

    def __init__(
        self,
        horizons_minutes: tuple[int, ...] = (1, 5, 15, 30, 60, 240, 1440),
        outlier_z_threshold: float = 3.0,
    ) -> None:
        self._horizons = tuple(sorted({minute for minute in horizons_minutes if minute > 0}))
        self._outlier_z_threshold = outlier_z_threshold

    def analyze(
        self,
        *,
        event_id: str,
        asset_symbol: str,
        event_time: datetime,
        observations: list[ReactionObservation],
    ) -> ReactionAnalysisResult:
        """Analyze reaction profile around one event from ordered observations."""
        if event_time.tzinfo is None:
            event_time = event_time.replace(tzinfo=timezone.utc)
        ordered = sorted(observations, key=lambda item: item.timestamp)
        if len(ordered) < 6:
            raise ValueError("at least 6 observations are required")

        pre_event = [item for item in ordered if item.timestamp <= event_time]
        if len(pre_event) < 3:
            raise ValueError("at least 3 pre-event observations are required")
        filtered_pre, pre_outliers = self._filter_price_outliers(pre_event)
        if len(filtered_pre) < 3:
            filtered_pre = pre_event
            pre_outliers = 0

        baseline_price = fmean([item.price for item in filtered_pre[-10:]])
        baseline_volume = max(1.0, fmean([item.volume for item in filtered_pre[-10:]]))
        baseline_volatility = self._volatility(filtered_pre[-20:])

        horizon_results: list[HorizonReaction] = []
        missing_horizons = 0
        for horizon in self._horizons:
            horizon_point = self._closest_point(
                ordered,
                target=event_time + timedelta(minutes=horizon),
                min_time=event_time,
            )
            if horizon_point is None:
                missing_horizons += 1
                continue
            post_slice = [item for item in ordered if event_time <= item.timestamp <= horizon_point.timestamp]
            post_volatility = self._volatility(post_slice)
            price_return_pct = ((horizon_point.price - baseline_price) / baseline_price) * 100
            volume_delta_pct = ((horizon_point.volume - baseline_volume) / baseline_volume) * 100
            volatility_delta_pct = 0.0
            if baseline_volatility > 0:
                volatility_delta_pct = ((post_volatility - baseline_volatility) / baseline_volatility) * 100
            elif post_volatility > 0:
                volatility_delta_pct = 100.0
            spread_delta = None
            if horizon_point.spread_bps is not None:
                baseline_spread = self._mean_optional([item.spread_bps for item in filtered_pre[-10:]])
                if baseline_spread is not None:
                    spread_delta = horizon_point.spread_bps - baseline_spread

            reaction_intensity = self._reaction_intensity(
                price_return_pct=price_return_pct,
                volume_delta_pct=volume_delta_pct,
                volatility_delta_pct=volatility_delta_pct,
            )
            horizon_results.append(
                HorizonReaction(
                    horizon_minutes=horizon,
                    price_return_pct=round(price_return_pct, 6),
                    volume_delta_pct=round(volume_delta_pct, 6),
                    volatility_delta_pct=round(volatility_delta_pct, 6),
                    spread_delta_bps=round(spread_delta, 6) if spread_delta is not None else None,
                    reaction_intensity=reaction_intensity,
                )
            )

        quality = {
            "observations_total": len(ordered),
            "pre_event_outliers_removed": pre_outliers,
            "horizons_requested": len(self._horizons),
            "horizons_measured": len(horizon_results),
            "horizons_missing": missing_horizons,
        }
        return ReactionAnalysisResult(
            event_id=event_id,
            asset_symbol=asset_symbol.upper(),
            measured_at=datetime.now(timezone.utc),
            baseline_price=round(baseline_price, 6),
            baseline_volume=round(baseline_volume, 6),
            baseline_volatility=round(baseline_volatility, 6),
            horizons=tuple(horizon_results),
            quality=quality,
        )

    @staticmethod
    def _closest_point(
        observations: list[ReactionObservation],
        *,
        target: datetime,
        min_time: datetime,
    ) -> ReactionObservation | None:
        candidate: ReactionObservation | None = None
        for item in observations:
            if item.timestamp < min_time:
                continue
            if item.timestamp > target:
                break
            candidate = item
        return candidate

    @staticmethod
    def _volatility(observations: list[ReactionObservation]) -> float:
        if len(observations) < 2:
            return 0.0
        returns: list[float] = []
        previous = observations[0].price
        for item in observations[1:]:
            if previous <= 0:
                previous = item.price
                continue
            returns.append((item.price - previous) / previous)
            previous = item.price
        if not returns:
            return 0.0
        mean = fmean(returns)
        variance = fmean([(item - mean) ** 2 for item in returns])
        return variance**0.5

    def _filter_price_outliers(
        self,
        observations: list[ReactionObservation],
    ) -> tuple[list[ReactionObservation], int]:
        prices = [item.price for item in observations]
        if len(prices) < 3:
            return observations, 0
        mean = fmean(prices)
        variance = fmean([(price - mean) ** 2 for price in prices])
        std_dev = variance**0.5
        if std_dev <= 0:
            return observations, 0
        filtered = [
            item
            for item in observations
            if abs((item.price - mean) / std_dev) <= self._outlier_z_threshold
        ]
        removed = len(observations) - len(filtered)
        return filtered, removed

    @staticmethod
    def _reaction_intensity(
        *,
        price_return_pct: float,
        volume_delta_pct: float,
        volatility_delta_pct: float,
    ) -> float:
        normalized_return = min(1.0, abs(price_return_pct) / 10.0)
        normalized_volume = min(1.0, abs(volume_delta_pct) / 200.0)
        normalized_volatility = min(1.0, abs(volatility_delta_pct) / 150.0)
        score = (normalized_return * 0.5) + (normalized_volume * 0.3) + (normalized_volatility * 0.2)
        return round(score, 6)

    @staticmethod
    def _mean_optional(values: list[float | None]) -> float | None:
        valid = [item for item in values if item is not None]
        if not valid:
            return None
        return fmean(valid)
