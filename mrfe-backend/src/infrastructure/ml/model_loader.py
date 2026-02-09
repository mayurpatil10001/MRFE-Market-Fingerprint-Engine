"""Async model loader with caching for ML inference utilities."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.core.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class TextClassificationResult:
    """Normalized text classification result."""

    label: str
    score: float
    sentiment: float


class AsyncModelLoader:
    """Load ML models lazily and cache them across requests."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._cache: dict[str, Any] = {}

    async def load_sklearn_model(self, model_path: str) -> Any | None:
        """Load a scikit-learn compatible model from disk."""
        key = f"sklearn::{model_path}"
        if key in self._cache:
            return self._cache[key]
        async with self._lock:
            if key in self._cache:
                return self._cache[key]
            path = Path(model_path)
            if not path.exists():
                logger.warning("sklearn_model_missing", path=str(path))
                self._cache[key] = None
                return None
            model = await asyncio.to_thread(self._load_joblib, path)
            self._cache[key] = model
            return model

    async def load_text_classifier(
        self,
        model_name: str,
        device: int = -1,
        local_files_only: bool = False,
    ) -> Any | None:
        """Load a transformer text-classification pipeline."""
        key = f"transformers::{model_name}::{device}::{local_files_only}"
        if key in self._cache:
            return self._cache[key]
        async with self._lock:
            if key in self._cache:
                return self._cache[key]
            pipeline = await asyncio.to_thread(
                self._load_transformer_pipeline,
                model_name,
                device,
                local_files_only,
            )
            self._cache[key] = pipeline
            return pipeline

    @staticmethod
    def _load_joblib(path: Path) -> Any | None:
        try:
            import joblib  # type: ignore[import-untyped]
        except ImportError:
            logger.warning("joblib_missing")
            return None
        try:
            return joblib.load(path)
        except Exception as exc:  # noqa: BLE001
            logger.warning("joblib_load_failed", error=str(exc), path=str(path))
            return None

    @staticmethod
    def _load_transformer_pipeline(
        model_name: str,
        device: int,
        local_files_only: bool,
    ) -> Any | None:
        try:
            from transformers import pipeline  # type: ignore[import-untyped]
        except ImportError:
            logger.warning("transformers_missing")
            return None
        try:
            return pipeline(
                "text-classification",
                model=model_name,
                tokenizer=model_name,
                device=device,
                local_files_only=local_files_only,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("transformer_load_failed", error=str(exc), model=model_name)
            return None


_MODEL_LOADER = AsyncModelLoader()


def get_model_loader() -> AsyncModelLoader:
    """Return shared model loader singleton."""
    return _MODEL_LOADER
