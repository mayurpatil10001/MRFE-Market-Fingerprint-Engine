"""Backtesting utilities for forecast evaluation."""

from __future__ import annotations

from math import sqrt
from typing import Iterable


def backtest_metrics(predictions: Iterable[float], actuals: Iterable[float]) -> dict[str, float]:
    """Compute MAE, RMSE, and directional accuracy."""
    preds = [float(value) for value in predictions]
    acts = [float(value) for value in actuals]
    if not preds or not acts:
        return {"mae": 0.0, "rmse": 0.0, "directional_accuracy": 0.0}
    length = min(len(preds), len(acts))
    preds = preds[:length]
    acts = acts[:length]
    errors = [abs(p - a) for p, a in zip(preds, acts, strict=False)]
    squared = [(p - a) ** 2 for p, a in zip(preds, acts, strict=False)]
    mae = sum(errors) / length
    rmse = sqrt(sum(squared) / length)
    correct = sum(1 for p, a in zip(preds, acts, strict=False) if (p >= 0) == (a >= 0))
    return {
        "mae": round(mae, 6),
        "rmse": round(rmse, 6),
        "directional_accuracy": round(correct / length, 6),
    }
