# ADR 0001: Clean Architecture + CQRS

## Status
Accepted

## Context
MRFE processes market-sensitive data and requires strict separation of domain logic from delivery and persistence concerns.

## Decision
Use Clean Architecture with DDD entities and CQRS use cases:
- Domain contracts (`repository`, `generator`, `detector`, `uow`) are pure Python.
- Infrastructure implements contracts via SQLAlchemy, Redis, and Celery.
- API layer only maps HTTP/WebSocket transport to application commands/queries.

## Consequences
- Clear boundaries improve testability and change safety.
- Additional boilerplate for command/query objects and dependency wiring.
