"""Unit tests for reaction analyzer."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from src.infrastructure.ml.reaction_analyzer import ReactionAnalyzer, ReactionObservation


def test_reaction_analyzer_generates_horizons() -> None:
    analyzer = ReactionAnalyzer(horizons_minutes=(1, 5))
    event_time = datetime.now(tz=UTC)
    observations = [
        ReactionObservation(timestamp=event_time - timedelta(minutes=10), price=100, volume=1000),
        ReactionObservation(timestamp=event_time - timedelta(minutes=5), price=101, volume=1100),
        ReactionObservation(timestamp=event_time - timedelta(minutes=1), price=100.5, volume=1050),
        ReactionObservation(timestamp=event_time + timedelta(minutes=1), price=102, volume=1200),
        ReactionObservation(timestamp=event_time + timedelta(minutes=5), price=103, volume=1250),
        ReactionObservation(timestamp=event_time + timedelta(minutes=10), price=101.5, volume=1150),
    ]
    result = analyzer.analyze(
        event_id="evt_1",
        asset_symbol="SPY",
        event_time=event_time,
        observations=observations,
    )
    assert result.horizons
    assert result.quality["horizons_measured"] >= 1
