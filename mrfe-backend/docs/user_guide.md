# User Guide

## Typical Workflow

1. Authenticate and obtain JWT token.
2. Detect or classify a market event.
3. Generate fingerprint for asset/event pair.
4. Generate forecast from fingerprint.
5. Monitor analytics and realtime stream.

## Realtime Stream

Use websocket endpoint:
- `ws://<host>/ws/realtime`
