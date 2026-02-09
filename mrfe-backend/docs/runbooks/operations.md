# MRFE Operational Runbook

## Incident Triage
1. Check health endpoints.
2. Check `mrfe_http_requests_total` and latency histogram.
3. Check recent errors in structured logs by `request_id`.
4. Verify DB connectivity and Redis queue depth.

## Rolling Deployment
1. Build and push new image tags.
2. Apply Kubernetes manifest updates.
3. Monitor readiness probes and error rates.
4. Roll back to previous image if error rate increases.

## Blue/Green Deployment
1. Deploy candidate to `green`.
2. Run synthetic checks.
3. Switch service selector to `green`.
4. Keep `blue` for rollback window.

## OpenRouter Key Management
1. Follow `docs/runbooks/openrouter_security.md` for rotation and incident response.
2. Validate budget caps before production rollout.

## On-Call Rotation
1. Primary/secondary weekly schedule.
2. Alert channels: email + Slack/PagerDuty bridge.
3. Handover notes required at rotation boundary.
