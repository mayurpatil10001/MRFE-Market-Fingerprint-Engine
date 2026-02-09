"""Similarity service for fingerprint embeddings and matching."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Iterable

from src.core.config.settings import settings
from src.core.logging import get_logger
from src.domain.entities.event import Event
from src.domain.entities.fingerprint import Fingerprint
from src.infrastructure.ml.feature_pipeline import MarketFeaturePipeline
from src.infrastructure.ml.fingerprint_vector_store import (
    FingerprintVectorStore,
    SimilarityMatch,
    SimilarityMatcher,
)

logger = get_logger(__name__)


class FingerprintSimilarityService:
    """Maintain fingerprint embeddings and perform similarity lookups."""

    def __init__(
        self,
        store_path: str | None = None,
        feature_pipeline: MarketFeaturePipeline | None = None,
        dimension: int | None = None,
        min_score: float | None = None,
    ) -> None:
        self._path = Path(store_path or settings.fingerprint_vector_store_path)
        self._dimension = dimension or settings.fingerprint_vector_dimension
        self._feature_pipeline = feature_pipeline or MarketFeaturePipeline()
        self._min_score = min_score or settings.similarity_min_score
        self._store = self._load_store()
        self._matcher = SimilarityMatcher(self._store, min_score=self._min_score)
        self._lock = asyncio.Lock()

    async def record(self, event: Event, fingerprint: Fingerprint, horizon_hours: int = 24) -> None:
        """Embed and persist a fingerprint vector with metadata."""
        vector = self._embed(event=event, fingerprint=fingerprint, horizon_hours=horizon_hours)
        metadata = {
            "asset_symbol": fingerprint.asset_symbol,
            "category": str(event.event_type),
            "reaction_intensity": f"{fingerprint.reaction_intensity:.4f}",
            "volatility_impact": f"{fingerprint.volatility_impact:.4f}",
            "volume_impact": f"{fingerprint.volume_impact:.4f}",
            "sentiment_score": f"{event.sentiment_score or 0.0:.4f}",
            "event_confidence": f"{event.confidence.value:.4f}",
        }
        async with self._lock:
            self._store.add(
                fingerprint_id=str(fingerprint.fingerprint_id),
                vector=vector,
                metadata=metadata,
            )
            self._persist()

    async def match(
        self,
        event: Event,
        fingerprint: Fingerprint,
        horizon_hours: int = 24,
        asset_symbol: str | None = None,
        category: str | None = None,
        top_k: int = 10,
    ) -> list[SimilarityMatch]:
        """Return similarity matches for the given fingerprint context."""
        vector = self._embed(event=event, fingerprint=fingerprint, horizon_hours=horizon_hours)
        return self._matcher.match(
            query_embedding=vector,
            top_k=top_k,
            asset_symbol=asset_symbol,
            category=category,
        )

    def _embed(self, event: Event, fingerprint: Fingerprint, horizon_hours: int) -> list[float]:
        features = self._feature_pipeline.build_forecast_features(
            event=event,
            fingerprint=fingerprint,
            forecast_horizon_hours=horizon_hours,
        )
        return features.as_list()

    def _persist(self) -> None:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._store.save(str(self._path))
        except Exception as exc:  # noqa: BLE001
            logger.warning("fingerprint_vector_store_save_failed", error=str(exc), path=str(self._path))

    def _load_store(self) -> FingerprintVectorStore:
        if self._path.exists():
            try:
                store = FingerprintVectorStore.load(str(self._path))
                if store.dimension != self._dimension:
                    logger.warning(
                        "fingerprint_vector_dimension_mismatch",
                        expected=self._dimension,
                        actual=store.dimension,
                    )
                    return FingerprintVectorStore(self._dimension)
                return store
            except Exception as exc:  # noqa: BLE001
                logger.warning("fingerprint_vector_store_load_failed", error=str(exc), path=str(self._path))
        return FingerprintVectorStore(self._dimension)


def mean_float(values: Iterable[float]) -> float:
    """Safe mean helper."""
    items = list(values)
    return sum(items) / len(items) if items else 0.0
