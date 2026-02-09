# OpenRouter Security Runbook

## Required Secrets

- `OPENROUTER_API_KEY`
- `OPENROUTER_BASE_URL` (default: `https://openrouter.ai/api/v1`)
- `OPENROUTER_PRIMARY_MODEL`
- `OPENROUTER_FALLBACK_MODEL`

## Budget and Guardrails

- Configure `OPENROUTER_MONTHLY_BUDGET_USD` to enforce a rolling in-process budget cap.
- Configure `OPENROUTER_MAX_COST_USD_PER_REQUEST` to hard-block expensive single calls.
- Monitor:
  - `mrfe_llm_requests_total`
  - `mrfe_llm_request_duration_seconds`
  - `mrfe_llm_tokens_total`
  - `mrfe_llm_cost_usd_total`

## API Key Rotation Procedure

1. Generate a replacement key in OpenRouter.
2. Store new key in your secret manager and CI/CD secret store.
3. Roll out key to non-production first.
4. Validate `/api/v1/intel/capabilities` and one `POST /api/v1/intel/brief` smoke test.
5. Promote to production and monitor error/cost metrics for 30 minutes.
6. Revoke the old key after successful production verification.

## Leak Response

1. Immediately revoke leaked key.
2. Rotate all affected environments.
3. Audit logs for abnormal LLM traffic patterns.
4. Temporarily lower budget thresholds to contain risk.
5. File an incident report with timeline and corrective actions.
