# MRFE 

Production-oriented backend for the Market Reaction Fingerprint Engine (MRFE), built with:
- FastAPI (async API adapters)
- Clean Architecture + DDD domain layer
- CQRS use cases with Unit of Work
- SQLAlchemy async repositories (PostgreSQL), optional Mongo read model, Redis cache
- Celery workers for asynchronous pipelines
- Prometheus/OpenTelemetry instrumentation

## Project Structure
See `docs/architecture.md` for the full layer model and dependency direction.
Additional docs:
- `docs/configuration.md`
- `docs/deployment.md`
- `docs/troubleshooting.md`
- `docs/api_usage.md`
- `docs/user_guide.md`
- `docs/faq.md`

## Quick Start
```bash
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000
```

Windows convenience:
- `d:\MRFE2\start_mrfe.bat` starts API + frontend.
- `d:\MRFE2\mrfe-backend\start_backend.bat` API only.
- `d:\MRFE2\mrfe-backend\start_frontend.bat` frontend only.

Docs:
- Frontend: `http://localhost:8000/`
- Swagger: `http://localhost:8000/docs`
- OpenAPI: `http://localhost:8000/openapi.json`
- Metrics: `http://localhost:8000/metrics`

## AI Intel Mode
`POST /api/v1/intel/brief` generates an institutional market brief.

- Uses `OPENROUTER_API_KEY` when configured.
- Falls back to deterministic heuristics if key is not available.
- Supports model fallback, retry/backoff, and usage/cost metrics.
- Supports configurable budget controls (`OPENROUTER_MONTHLY_BUDGET_USD`, `OPENROUTER_MAX_COST_USD_PER_REQUEST`).

## ML Enhancements
- Transformer sentiment classification for event detection (`EVENT_CLASSIFIER_MODEL`).
- ML-driven fingerprint generation with fallback to deterministic mode.
- Similarity-aware ensemble forecasting with Monte Carlo confidence intervals.
- Backtest endpoint: `POST /api/v1/forecasts/backtest`.

## MLOps Upgrades
- `GET /api/v1/ml/models`: model registry listing
- `POST /api/v1/ml/models/register`: register staging model candidate
- `POST /api/v1/ml/models/{model_id}/promote`: promote to `production|canary|shadow`
- `POST /api/v1/ml/drift/check`: Jensen-Shannon drift detection with optional retraining enqueue

Forecast generation now uses an advanced ensemble strategy with regime-aware calibration.

## Run Tests
```bash
pytest
```

## Frontend (React + TypeScript)
```bash
cd frontend
npm install
npm run dev
npm run test
npm run build
```

## Data Collection
```bash
python scripts/data/collect_daily.py
```

## NewsAPI Ingest (No Auto Events)
- Configure `NEWSAPI_API_KEY` and optional `NEWSAPI_QUERY`.
- Refresh news cache: `POST /api/v1/news/refresh`.

## Continuous Learning Endpoints

- `POST /api/v1/ml/learning/incremental-update`
- `POST /api/v1/ml/regime/detect`
- `GET /api/v1/ml/retraining/schedule`

## Docker
```bash
docker compose up --build
```

## Migrations
```bash
alembic upgrade head
```

## Deployment
- Kubernetes manifests: `kubernetes/`
- Helm chart: `helm/mrfe/`
- CI pipeline: `.github/workflows/ci.yml`
- CD workflow: `.github/workflows/deploy.yml`
- OpenRouter security runbook: `docs/runbooks/openrouter_security.md`
