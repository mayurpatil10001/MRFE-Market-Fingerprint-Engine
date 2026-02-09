# Troubleshooting

## API returns 401

- Ensure either:
  - `Authorization: Bearer <token>` is present, or
  - `X-API-Key` matches `SERVICE_API_KEYS_CSV`.

## OpenRouter unavailable

- Verify `OPENROUTER_API_KEY`.
- Check `/api/v1/intel/capabilities`.
- Inspect metrics:
  - `mrfe_llm_requests_total`
  - `mrfe_llm_request_duration_seconds`

## Rate limit exceeded

- Tune `RATE_LIMIT_PER_MINUTE` for environment.
- Check request fanout from clients/load tests.

## Frontend cannot reach API

- In local dev, run backend on `:8000` and frontend on `:5173`.
- Verify Vite proxy in `frontend/vite.config.ts`.
