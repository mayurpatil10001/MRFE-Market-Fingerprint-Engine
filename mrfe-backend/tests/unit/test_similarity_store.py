"""Unit tests for vector store and similarity matcher."""

from __future__ import annotations

from src.infrastructure.ml.fingerprint_vector_store import FingerprintVectorStore, SimilarityMatcher


def test_vector_store_knn_and_filters() -> None:
    store = FingerprintVectorStore(dimension=3)
    store.add("fp_1", [0.1, 0.2, 0.3], {"asset_symbol": "SPY", "category": "macro"})
    store.add("fp_2", [0.9, 0.9, 0.9], {"asset_symbol": "QQQ", "category": "earnings"})
    matches = store.knn([0.1, 0.2, 0.31], top_k=2, asset_symbol="SPY")
    assert len(matches) == 1
    assert matches[0].fingerprint_id == "fp_1"
    assert 0.0 <= matches[0].score <= 1.0


def test_similarity_matcher_applies_threshold() -> None:
    store = FingerprintVectorStore(dimension=2)
    store.add("near", [0.1, 0.1], {})
    store.add("far", [10.0, 10.0], {})
    matcher = SimilarityMatcher(store=store, min_score=0.5)
    matches = matcher.match([0.1, 0.09], top_k=2)
    assert len(matches) == 1
    assert matches[0].fingerprint_id == "near"
