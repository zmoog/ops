# looter

Custom OpenTelemetry Collector distro for experimentation.

- Source: <https://github.com/zmoog/looter>
- Image: `ghcr.io/zmoog/looter`

## homelab-kind

Deployed into the `looter` namespace by Argo CD.

Service endpoints inside the cluster:

- OTLP gRPC: `looter.looter.svc.cluster.local:4317`
- OTLP HTTP: `http://looter.looter.svc.cluster.local:4318`
- Health check: `http://looter.looter.svc.cluster.local:13133/`
- pprof: `http://looter.looter.svc.cluster.local:1777`
- zPages: `http://looter.looter.svc.cluster.local:55679`
