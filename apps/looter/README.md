# looter

Custom OpenTelemetry Collector distro for experimentation.

- Source: <https://github.com/zmoog/looter>
- Image: `ghcr.io/zmoog/looter`

## homelab-kind

Deployed into the `observability` namespace by Argo CD.

Service endpoints inside the cluster:

- OTLP gRPC: `looter.observability.svc.cluster.local:4317`
- OTLP HTTP: `http://looter.observability.svc.cluster.local:4318`
- Health check: `http://looter.observability.svc.cluster.local:13133/`
- pprof: `http://looter.observability.svc.cluster.local:1777`
- zPages: `http://looter.observability.svc.cluster.local:55679`
