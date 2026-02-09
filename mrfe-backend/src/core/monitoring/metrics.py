"""Prometheus metrics primitives."""

from __future__ import annotations

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

http_requests_total = Counter(
    "mrfe_http_requests_total",
    "Total HTTP requests",
    ("method", "path", "status_code"),
)
http_request_duration_seconds = Histogram(
    "mrfe_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ("method", "path"),
    buckets=(0.01, 0.025, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0),
)
active_requests = Gauge("mrfe_http_active_requests", "Current in-flight requests")
event_detection_total = Counter(
    "mrfe_event_detection_total",
    "Number of detect-event executions",
    ("source",),
)
slow_query_total = Counter(
    "mrfe_slow_query_total",
    "Number of slow queries",
    ("query_name",),
)
ml_drift_alert_total = Counter(
    "mrfe_ml_drift_alert_total",
    "Number of model drift alerts",
    ("model_version", "status"),
)
ml_registry_updates_total = Counter(
    "mrfe_ml_registry_updates_total",
    "Number of model registry mutations",
    ("action",),
)
llm_requests_total = Counter(
    "mrfe_llm_requests_total",
    "Total LLM requests by provider/model/status",
    ("provider", "model", "status"),
)
llm_request_duration_seconds = Histogram(
    "mrfe_llm_request_duration_seconds",
    "LLM request latency in seconds",
    ("provider", "model"),
    buckets=(0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0),
)
llm_tokens_total = Counter(
    "mrfe_llm_tokens_total",
    "LLM token usage by provider/model/token type",
    ("provider", "model", "token_type"),
)
llm_cost_usd_total = Counter(
    "mrfe_llm_cost_usd_total",
    "Estimated LLM cost in USD by provider/model",
    ("provider", "model"),
)


def export_metrics() -> tuple[bytes, str]:
    """Return metrics payload + content-type."""
    return generate_latest(), CONTENT_TYPE_LATEST
