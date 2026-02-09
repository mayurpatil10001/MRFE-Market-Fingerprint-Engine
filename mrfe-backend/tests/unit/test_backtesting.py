"""Unit tests for backtesting metrics."""

from __future__ import annotations

from src.infrastructure.ml.backtesting import backtest_metrics


def test_backtest_metrics_directional_accuracy() -> None:
    metrics = backtest_metrics([0.1, -0.2, 0.05], [0.12, -0.1, -0.01])
    assert metrics["mae"] >= 0
    assert metrics["rmse"] >= 0
    assert 0.0 <= metrics["directional_accuracy"] <= 1.0
