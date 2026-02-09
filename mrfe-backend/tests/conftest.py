"""Shared test fixtures."""

from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_mrfe.db")
os.environ.setdefault("JWT_PRIVATE_KEY", "test-private-key")
os.environ.setdefault("JWT_PUBLIC_KEY", "test-private-key")
os.environ["JWT_ALGORITHM"] = "RS256"
os.environ["OTEL_ENABLED"] = "false"
os.environ["ENVIRONMENT"] = "testing"
os.environ["MODEL_REGISTRY_PATH"] = "./test_model_registry.json"

from src.main import app  # noqa: E402


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    """FastAPI test client."""
    registry_file = Path("./test_model_registry.json")
    if registry_file.exists():
        registry_file.unlink()
    with TestClient(app) as test_client:
        yield test_client
    if registry_file.exists():
        registry_file.unlink()
