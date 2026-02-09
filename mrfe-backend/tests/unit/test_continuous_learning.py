"""Unit tests for continuous learning utilities."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from src.infrastructure.ml.continuous_learning import (
    IncrementalLearner,
    RegimeDetector,
    RetrainingScheduler,
)


def test_incremental_learner_updates_centroid() -> None:
    learner = IncrementalLearner(dimension=3)
    first = learner.update([1.0, 0.0, 0.0])
    second = learner.update([0.0, 1.0, 0.0])
    assert first == [1.0, 0.0, 0.0]
    assert learner.observations == 2
    assert second[0] == 0.5
    assert second[1] == 0.5


def test_regime_detector_outputs_known_regime() -> None:
    detector = RegimeDetector()
    state = detector.detect([0.02, 0.01, -0.005, 0.008])
    assert state.regime in {"bull", "bear", "volatile", "sideways", "unknown"}


def test_retraining_scheduler_due_logic() -> None:
    scheduler = RetrainingScheduler(interval_hours=1)
    assert scheduler.due()
    scheduler.mark_run()
    assert not scheduler.due(now=datetime.now(tz=UTC) + timedelta(minutes=30))
    assert scheduler.due(now=datetime.now(tz=UTC) + timedelta(hours=2))
