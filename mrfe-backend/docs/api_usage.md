# API Usage Guide

## Authentication

### JWT flow
- `POST /api/v1/auth/token`
- `POST /api/v1/auth/refresh`

### Service account flow
- Supply `X-API-Key` matching `SERVICE_API_KEYS_CSV`.

## Core Endpoints

- `POST /api/v1/events/detect`
- `POST /api/v1/events/classify`
- `GET /api/v1/events`
- `POST /api/v1/fingerprints`
- `GET /api/v1/fingerprints`
- `POST /api/v1/forecasts`
- `GET /api/v1/forecasts`
- `POST /api/v1/forecasts/backtest`
- `POST /api/v1/reactions/measure`
- `POST /api/v1/reactions/measure-and-store`
- `POST /api/v1/reactions/analyze`
- `GET /api/v1/reactions`
- `GET /api/v1/news`
- `POST /api/v1/news/refresh`
- `POST /api/v1/intel/brief`
- `POST /api/v1/ml/learning/incremental-update`
- `POST /api/v1/ml/regime/detect`
- `GET /api/v1/ml/retraining/schedule`
