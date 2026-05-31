# ops

GitOps repo for personal workloads.

## Structure

- `apps/<name>/chart`: Helm chart for one app
- `apps/<name>/secrets`: local secret templates (`*.example.yaml` tracked)
- `clusters/<cluster-name>`: cluster bootstrap and app-of-apps manifests
- `argocd/applications`: standalone Argo CD `Application` manifests

## Current apps

- `ifq`: daily IFQ download CronJob (uploads PDF to Dropbox)
- `otel-collector-gateway`: cluster-level OTel gateway (OTLP traces + k8s cluster metrics)

## Clusters

- `clusters/homelab-kind`: Kind-on-LAN setup with ingress-nginx, ifq, and otel-collector-gateway
