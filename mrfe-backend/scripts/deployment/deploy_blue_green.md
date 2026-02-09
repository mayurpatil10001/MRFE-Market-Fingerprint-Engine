# Blue/Green Deploy Steps

1. Deploy new release to `deployment-green.yaml`.
2. Run smoke checks against green service endpoint.
3. Switch ingress/service selector to green.
4. Keep blue deployment for rollback window.
5. Scale blue down after validation window.
