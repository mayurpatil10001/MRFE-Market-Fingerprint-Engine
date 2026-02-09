# Deployment Guide

## Docker Compose

```bash
docker compose up --build
```

Services:
- `api` (FastAPI)
- `worker` (Celery)
- `beat` (Celery scheduler for daily data collection + retention)
- `frontend` (Vite static bundle via Nginx)
- `postgres`
- `mongo`
- `redis`

## Kubernetes

Base manifests are in `kubernetes/`.
Helm chart is in `helm/mrfe/`.

## CI/CD

- CI: `.github/workflows/ci.yml`
- CD: `.github/workflows/deploy.yml`

CD workflow currently includes environment-gated skeleton jobs and secret checks.
It expects kubeconfig secrets (`KUBE_CONFIG_DEV`, `KUBE_CONFIG_STAGING`, `KUBE_CONFIG_PROD`) to be base64 encoded.
