# OTel Collector Gateway

Cluster-level OTel collector for:
- receiving OTLP traces from apps (e.g. `ifq-job`)
- collecting Kubernetes cluster metrics (`k8s_cluster` receiver)

## Local install on Kind

```bash
kubectl --context kind-kind create ns observability --dry-run=client -o yaml | kubectl apply -f -
cp apps/otel-collector-gateway/secrets/backend.example.yaml apps/otel-collector-gateway/secrets/backend.yaml
# edit apps/otel-collector-gateway/secrets/backend.yaml
kubectl --context kind-kind apply -n observability -f apps/otel-collector-gateway/secrets/backend.yaml

helm upgrade --install otel-collector-gateway apps/otel-collector-gateway/chart \
  --kube-context kind-kind \
  --namespace observability \
  -f apps/otel-collector-gateway/chart/values-kind.yaml
```

## Collector endpoints

- OTLP gRPC: `otel-collector-gateway.observability.svc.cluster.local:4317`
- OTLP HTTP: `otel-collector-gateway.observability.svc.cluster.local:4318`

## Notes

- Kind values enable backend export by default (`backend.enabled=true`).
- Backend endpoint and auth header are read from secret `otel-backend`:
  - `OTEL_BACKEND_OTLP_ENDPOINT`
  - `OTEL_BACKEND_OTLP_AUTH_HEADER` (optional)
