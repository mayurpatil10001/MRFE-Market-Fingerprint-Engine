"""OpenTelemetry setup helpers."""

from __future__ import annotations

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

from src.core.config.settings import settings


def configure_tracing(app: FastAPI) -> None:
    """Enable tracing for FastAPI app."""
    if not settings.otel_enabled:
        return
    provider = TracerProvider(resource=Resource(attributes={SERVICE_NAME: "mrfe-backend"}))
    provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app)
