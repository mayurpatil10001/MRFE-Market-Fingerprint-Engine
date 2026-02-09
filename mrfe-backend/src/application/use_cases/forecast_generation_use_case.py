"""Use case for GenerateForecastCommand."""

from __future__ import annotations

from src.application.dto.commands import GenerateForecastCommand
from src.application.dto.responses import ForecastResponseDTO
from src.application.use_cases.mappers import to_forecast_dto
from src.domain.entities.forecast import Forecast
from src.domain.exceptions import EventNotFoundError, FingerprintNotFoundError
from src.domain.interfaces import ForecastGenerator, UnitOfWork
from src.domain.value_objects.confidence import Confidence
from src.domain.value_objects.event_id import EventId


class GenerateForecastUseCase:
    """Generate probabilistic forecast from event + fingerprint."""

    def __init__(self, uow: UnitOfWork, generator: ForecastGenerator) -> None:
        self._uow = uow
        self._generator = generator

    async def execute(self, command: GenerateForecastCommand) -> ForecastResponseDTO:
        """Generate and persist forecast."""
        event_id = EventId.from_string(command.event_id)
        fingerprint_id = EventId.from_string(command.fingerprint_id)
        async with self._uow:
            event = await self._uow.events.get_by_id(event_id)
            if event is None:
                raise EventNotFoundError("event not found")
            fingerprint = await self._uow.fingerprints.get_by_id(fingerprint_id)
            if fingerprint is None:
                raise FingerprintNotFoundError("fingerprint not found")
            result = await self._generator.generate(
                event=event,
                fingerprint=fingerprint,
                asset_symbol=command.asset_symbol,
                forecast_horizon_hours=command.forecast_horizon_hours,
                model_version=command.model_version,
            )
            forecast = Forecast.create(
                event_id=event_id,
                fingerprint_id=fingerprint_id,
                asset_symbol=command.asset_symbol,
                forecast_horizon_hours=command.forecast_horizon_hours,
                probability_distribution=result.probability_distribution,
                predicted_movement=result.predicted_movement,
                confidence=Confidence(result.confidence),
                risk_metrics=result.risk_metrics,
                model_version=command.model_version,
            )
            await self._uow.forecasts.add(forecast)
            await self._uow.commit()
        return to_forecast_dto(forecast)
