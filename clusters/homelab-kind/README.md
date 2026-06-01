# homelab-kind

Kind cluster profile for LAN-hosted homelab services.

## What it deploys (via Argo app-of-apps)

- `ingress-nginx` (host ports 80/443)
- `otel-collector-gateway`
- `ifq`
- `home-telemetry-collector`

## 1) Create Kind cluster

```bash
kind create cluster --config clusters/homelab-kind/kind-config.yaml --name homelab-kind
```

## 2) Install Argo CD

```bash
kubectl --context kind-homelab-kind create namespace argocd
kubectl --context kind-homelab-kind apply -n argocd \
  -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

## 3) Create required secrets

```bash
kubectl --context kind-homelab-kind create ns ifq --dry-run=client -o yaml | kubectl apply -f -
kubectl --context kind-homelab-kind create ns observability --dry-run=client -o yaml | kubectl apply -f -
kubectl --context kind-homelab-kind create ns home-telemetry --dry-run=client -o yaml | kubectl apply -f -

cp apps/ifq/secrets/ifq-secret.example.yaml apps/ifq/secrets/ifq-secret.yaml
cp apps/otel-collector-gateway/secrets/backend.example.yaml apps/otel-collector-gateway/secrets/backend.yaml
cp apps/home-telemetry-collector/secrets/collector-secret.example.yaml apps/home-telemetry-collector/secrets/collector-secret.yaml
# edit all files, then apply:
kubectl --context kind-homelab-kind apply -n ifq -f apps/ifq/secrets/ifq-secret.yaml
kubectl --context kind-homelab-kind apply -n observability -f apps/otel-collector-gateway/secrets/backend.yaml
kubectl --context kind-homelab-kind apply -n home-telemetry -f apps/home-telemetry-collector/secrets/collector-secret.yaml
```

## 4) Bootstrap app-of-apps

```bash
kubectl --context kind-homelab-kind apply -f clusters/homelab-kind/root-app.yaml
```

## 5) LAN access

Point LAN DNS (or hosts entries) to your Raspberry Pi IP for domains you expose via ingress.
