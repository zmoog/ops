# ops

GitOps repo for personal workloads.

## Structure

- `apps/<name>/chart`: Helm chart for one app
- `apps/<name>/secrets`: local secret templates (`*.example.yaml` tracked)
- `clusters/<cluster-name>`: cluster bootstrap and app-of-apps manifests

## Current apps

- `ifq`: daily IFQ download CronJob (uploads PDF to Dropbox)
- `otel-collector-gateway`: cluster-level OTel gateway (OTLP traces + k8s cluster metrics)
- `home-telemetry-collector`: collector for solar/HVAC/energy + toggl telemetry

## Clusters

- `clusters/homelab-kind`: Kind-on-LAN setup with ingress-nginx, ifq, otel-collector-gateway, and home-telemetry-collector
