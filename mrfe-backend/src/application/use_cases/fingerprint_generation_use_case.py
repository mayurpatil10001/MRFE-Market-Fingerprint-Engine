"""Use case for GenerateFingerprintCommand and UpdateFingerprintCommand."""

from __future__ import annotations

from src.application.dto.commands import GenerateFingerprintCommand, UpdateFingerprintCommand
from src.application.dto.responses import FingerprintResponseDTO
from src.application.use_cases.mappers import to_fingerprint_dto
from src.domain.entities.fingerprint import Fingerprint
from src.domain.exceptions import EventNotFoundError, FingerprintNotFoundError
from src.domain.interfaces import FingerprintGenerator, UnitOfWork
from src.infrastructure.ml.similarity_service import FingerprintSimilarityService
from src.domain.value_objects.confidence import Confidence
from src.domain.value_objects.event_id import EventId


class GenerateFingerprintUseCase:
    """Generate fingerprint for one event-asset pair."""

    def __init__(
        self,
        uow: UnitOfWork,
        generator: FingerprintGenerator,
        similarity_service: FingerprintSimilarityService | None = None,
    ) -> None:
        self._uow = uow
        self._generator = generator
        self._similarity_service = similarity_service

    async def execute(self, command: GenerateFingerprintCommand) -> FingerprintResponseDTO:
        """Generate and persist fingerprint in one transaction."""
        event_id = EventId.from_string(command.event_id)
        async with self._uow:
            event = await self._uow.events.get_by_id(event_id)
            if event is None:
                raise EventNotFoundError("event not found")
            generation = await self._generator.generate(
                event=event,
                asset_symbol=command.asset_symbol,
                model_version=command.model_version,
            )
            fingerprint = Fingerprint.create(
                event_id=event_id,
                asset_symbol=command.asset_symbol,
                reaction_patterns=generation.reaction_patterns,
                baseline_metrics=generation.baseline_metrics,
                reaction_intensity=generation.reaction_intensity,
                duration_minutes=generation.duration_minutes,
                volatility_impact=generation.volatility_impact,
                volume_impact=generation.volume_impact,
                confidence=Confidence(generation.confidence),
                model_version=command.model_version,
            )
            await self._uow.fingerprints.add(fingerprint)
            await self._uow.commit()
        if self._similarity_service is not None:
            await self._similarity_service.record(event=event, fingerprint=fingerprint)
        return to_fingerprint_dto(fingerprint)


class UpdateFingerprintUseCase:
    """Update mutable fingerprint fields."""

    def __init__(self, uow: UnitOfWork, similarity_service: FingerprintSimilarityService | None = None) -> None:
        self._uow = uow
        self._similarity_service = similarity_service

    async def execute(self, command: UpdateFingerprintCommand) -> FingerprintResponseDTO:
        """Apply update and persist."""
        fingerprint_id = EventId.from_string(command.fingerprint_id)
        async with self._uow:
            fingerprint = await self._uow.fingerprints.get_by_id(fingerprint_id)
            if fingerprint is None:
                raise FingerprintNotFoundError("fingerprint not found")
            fingerprint.update(
                reaction_intensity=command.reaction_intensity,
                volatility_impact=command.volatility_impact,
                volume_impact=command.volume_impact,
            )
            await self._uow.fingerprints.update(fingerprint)
            event = await self._uow.events.get_by_id(fingerprint.event_id)
            await self._uow.commit()
        if self._similarity_service is not None:
            if event is not None:
                await self._similarity_service.record(event=event, fingerprint=fingerprint)
        return to_fingerprint_dto(fingerprint)
