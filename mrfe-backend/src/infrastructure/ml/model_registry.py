"""File-backed model registry for enterprise ML lifecycle management."""

from __future__ import annotations

import asyncio
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.core.config.settings import settings


@dataclass(frozen=True, slots=True)
class ModelRecord:
    """Immutable model registry record."""

    model_id: str
    name: str
    version: str
    framework: str
    artifact_uri: str
    stage: str
    created_at: str
    tags: dict[str, str]


class ModelRegistryService:
    """Persist and manage model metadata with stage transitions."""

    _lock = asyncio.Lock()

    def __init__(self, registry_path: str | None = None) -> None:
        self._path = Path(registry_path or settings.model_registry_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    async def list_models(self) -> list[ModelRecord]:
        """Return all model records sorted by create time descending."""
        payload = await self._read_payload()
        models = [self._from_dict(item) for item in payload]
        return sorted(models, key=lambda item: item.created_at, reverse=True)

    async def register_model(
        self,
        name: str,
        version: str,
        framework: str,
        artifact_uri: str,
        tags: dict[str, str],
    ) -> ModelRecord:
        """Register new model in staging."""
        async with self._lock:
            payload = await self._read_payload()
            record = ModelRecord(
                model_id=str(uuid4()),
                name=name,
                version=version,
                framework=framework,
                artifact_uri=artifact_uri,
                stage="staging",
                created_at=datetime.now(timezone.utc).isoformat(),
                tags=tags,
            )
            payload.append(asdict(record))
            await self._write_payload(payload)
        return record

    async def promote_model(self, model_id: str, stage: str = "production") -> ModelRecord:
        """Promote model by id and demote previous model in target stage."""
        async with self._lock:
            payload = await self._read_payload()
            updated: dict[str, Any] | None = None
            for item in payload:
                if item.get("stage") == stage and item.get("model_id") != model_id:
                    item["stage"] = "archived"
                if item.get("model_id") == model_id:
                    item["stage"] = stage
                    updated = item
            if updated is None:
                raise ValueError("model_id not found")
            await self._write_payload(payload)
        return self._from_dict(updated)

    async def get_active_model(self, stage: str = "production") -> ModelRecord | None:
        """Return most recent model for stage."""
        models = await self.list_models()
        for model in models:
            if model.stage == stage:
                return model
        return None

    async def _read_payload(self) -> list[dict[str, Any]]:
        if not self._path.exists():
            return []
        raw = self._path.read_text(encoding="utf-8")
        if not raw.strip():
            return []
        data = json.loads(raw)
        return data if isinstance(data, list) else []

    async def _write_payload(self, payload: list[dict[str, Any]]) -> None:
        self._path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @staticmethod
    def _from_dict(data: dict[str, Any]) -> ModelRecord:
        return ModelRecord(
            model_id=str(data["model_id"]),
            name=str(data["name"]),
            version=str(data["version"]),
            framework=str(data["framework"]),
            artifact_uri=str(data["artifact_uri"]),
            stage=str(data["stage"]),
            created_at=str(data["created_at"]),
            tags={str(key): str(value) for key, value in dict(data.get("tags", {})).items()},
        )
