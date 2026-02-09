# Scaling Guide

## Horizontal Scaling

- API: increase replicas and tune HPA.
- Worker: scale Celery workers by queue depth and latency.

## Vertical Scaling

- Tune DB pool size and Redis memory limits.
- Increase CPU for forecast-heavy workloads.

## LLM Scaling

- Monitor per-model latency and cost metrics.
- Shift lower-priority traffic to cheaper fallback models when budget pressure increases.
