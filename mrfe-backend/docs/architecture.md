# MRFE Backend Architecture

## Principles
- Clean Architecture with strict dependency flow (`api -> application -> domain`, `infrastructure` implementing ports).
- Domain-Driven Design with rich aggregates and immutable value objects.
- CQRS split between command use cases and query use cases.
- Unit of Work transaction boundary for all write operations.

## Layers
- `src/domain`: entities, value objects, events, specifications, and repository/service contracts.
- `src/application`: Pydantic command/query DTOs and use-case handlers.
- `src/infrastructure`: SQLAlchemy repositories, Mongo repository, cache, messaging, workers.
- `src/infrastructure/data_collection`: market/news/macro ingestion collectors.
- `src/infrastructure/ml`: event detection, ensemble forecast, drift monitoring, similarity vector store.
- `src/infrastructure/ml/model_loader.py`: async ML model loader and cache (transformers + sklearn).
- `src/infrastructure/ml/similarity_service.py`: embedding storage and similarity matching.
- `src/api`: FastAPI adapters (REST + WebSocket), middleware, auth.
- `src/core`: configuration, logging, monitoring, shared security primitives.
- `frontend/`: React + TypeScript client (Vite).

## Reliability and Security
- RS256 JWT with refresh rotation and RBAC role checks.
- Rate limiting middleware (IP/auth identity).
- Structured JSON logs with request correlation.
- Prometheus metrics and OpenTelemetry tracing hook.
- Health probes (`/api/v1/health/live`, `/api/v1/health/ready`).
