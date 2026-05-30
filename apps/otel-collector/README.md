# OTel Collector Gateway

Cluster-level OTel collector for:
- receiving OTLP traces from apps (e.g. `ifq-job`)
- collecting Kubernetes cluster metrics (`k8s_cluster` receiver)

## Local install on Kind

```bash
kubectl --context kind-kind create ns observability --dry-run=client -o yaml | kubectl apply -f -
helm upgrade --install otel-collector-gateway apps/otel-collector/chart \
  --kube-context kind-kind \
  --namespace observability \
  -f apps/otel-collector/chart/values-kind.yaml
```

## Collector endpoints

- OTLP gRPC: `otel-collector-gateway.observability.svc.cluster.local:4317`
- OTLP HTTP: `otel-collector-gateway.observability.svc.cluster.local:4318`

## Notes

- By default, exporter to external backend is disabled.
- To forward data, set:
  - `exporters.otlp.enabled=true`
  - `exporters.otlp.endpoint`
  - optional `exporters.otlp.headers`
