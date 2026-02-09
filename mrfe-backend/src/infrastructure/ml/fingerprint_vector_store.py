"""Vector store and similarity matching for fingerprints."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class SimilarityMatch:
    """Similarity lookup result."""

    fingerprint_id: str
    score: float
    distance: float
    metadata: dict[str, str]


class FingerprintVectorStore:
    """Simple vector index with optional FAISS acceleration."""

    def __init__(self, dimension: int) -> None:
        self._dimension = dimension
        self._vectors: list[list[float]] = []
        self._ids: list[str] = []
        self._metadata: list[dict[str, str]] = []
        self._faiss_index: Any | None = None
        self._initialize_faiss()

    @property
    def dimension(self) -> int:
        """Embedding dimension."""
        return self._dimension

    def add(self, fingerprint_id: str, vector: list[float], metadata: dict[str, str] | None = None) -> None:
        """Insert one vector embedding."""
        normalized = self._normalize(vector)
        if fingerprint_id in self._ids:
            index = self._ids.index(fingerprint_id)
            self._vectors[index] = normalized
            self._metadata[index] = metadata or {}
            if self._faiss_index is not None:
                self._faiss_index = None
                self._initialize_faiss()
                if self._faiss_index is not None:
                    self._faiss_index.add(self._to_numpy(self._vectors))
            return
        self._ids.append(fingerprint_id)
        self._vectors.append(normalized)
        self._metadata.append(metadata or {})
        if self._faiss_index is not None:
            self._faiss_index.add(self._to_numpy([normalized]))

    def knn(
        self,
        query: list[float],
        top_k: int = 10,
        asset_symbol: str | None = None,
        category: str | None = None,
    ) -> list[SimilarityMatch]:
        """Search nearest fingerprints by L2 distance and convert to similarity."""
        if not self._vectors:
            return []
        query_vec = self._normalize(query)
        candidate_indexes = self._filtered_indexes(asset_symbol=asset_symbol, category=category)
        ranked: list[SimilarityMatch] = []
        for index in candidate_indexes:
            distance = self._l2_distance(query_vec, self._vectors[index])
            score = 1 / (1 + distance)
            ranked.append(
                SimilarityMatch(
                    fingerprint_id=self._ids[index],
                    score=round(score, 6),
                    distance=round(distance, 6),
                    metadata=self._metadata[index],
                )
            )
        ranked.sort(key=lambda item: item.distance)
        return ranked[:top_k]

    def save(self, path: str) -> Path:
        """Persist vector index and metadata to disk."""
        payload = {
            "dimension": self._dimension,
            "ids": self._ids,
            "vectors": self._vectors,
            "metadata": self._metadata,
        }
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload), encoding="utf-8")
        return target

    @classmethod
    def load(cls, path: str) -> "FingerprintVectorStore":
        """Load vector store from disk."""
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        store = cls(dimension=int(payload["dimension"]))
        ids = payload.get("ids", [])
        vectors = payload.get("vectors", [])
        metadata = payload.get("metadata", [])
        for fingerprint_id, vector, meta in zip(ids, vectors, metadata, strict=False):
            if isinstance(fingerprint_id, str) and isinstance(vector, list):
                store.add(fingerprint_id=fingerprint_id, vector=[float(v) for v in vector], metadata=dict(meta))
        return store

    def _filtered_indexes(self, asset_symbol: str | None, category: str | None) -> list[int]:
        indexes: list[int] = []
        for index, meta in enumerate(self._metadata):
            if asset_symbol and meta.get("asset_symbol") != asset_symbol:
                continue
            if category and meta.get("category") != category:
                continue
            indexes.append(index)
        return indexes

    def _initialize_faiss(self) -> None:
        try:
            import faiss  # type: ignore[import-untyped]
        except ImportError:
            self._faiss_index = None
            return
        self._faiss_index = faiss.IndexFlatL2(self._dimension)

    @staticmethod
    def _l2_distance(left: list[float], right: list[float]) -> float:
        return math.sqrt(
            sum((left_value - right_value) ** 2 for left_value, right_value in zip(left, right, strict=True))
        )

    def _normalize(self, vector: list[float]) -> list[float]:
        if len(vector) != self._dimension:
            raise ValueError(f"expected vector size {self._dimension}, got {len(vector)}")
        return [float(value) for value in vector]

    @staticmethod
    def _to_numpy(vectors: list[list[float]]) -> Any:
        import numpy as np

        return np.array(vectors, dtype="float32")


class SimilarityMatcher:
    """Higher-level matching API wrapping the vector store."""

    def __init__(self, store: FingerprintVectorStore, min_score: float = 0.6) -> None:
        self._store = store
        self._min_score = min_score

    def match(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        asset_symbol: str | None = None,
        category: str | None = None,
    ) -> list[SimilarityMatch]:
        """Return top matches filtered by minimum confidence score."""
        matches = self._store.knn(
            query=query_embedding,
            top_k=top_k,
            asset_symbol=asset_symbol,
            category=category,
        )
        return [item for item in matches if item.score >= self._min_score]
