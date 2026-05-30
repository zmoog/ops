# IFQ app (Helm)

This deploys the IFQ downloader CronJob.

## Local test on Kind

1) Build and load image (from `/Users/zmoog/code/zmoog/ifq-job/main`):

```bash
cd /Users/zmoog/code/zmoog/ifq-job/main
docker build -t ghcr.io/zmoog/ifq-job:latest .
kind load docker-image ghcr.io/zmoog/ifq-job:latest --name kind
```

2) Create secret:

```bash
cp apps/ifq/secrets/ifq-secret.example.yaml apps/ifq/secrets/ifq-secret.yaml
# edit apps/ifq/secrets/ifq-secret.yaml
kubectl --context kind-kind apply -n ifq -f apps/ifq/secrets/ifq-secret.yaml
```

3) Install chart:

```bash
kubectl --context kind-kind create ns ifq --dry-run=client -o yaml | kubectl apply -f -
helm upgrade --install ifq apps/ifq/chart \
  --kube-context kind-kind \
  --namespace ifq \
  -f apps/ifq/chart/values-kind.yaml
```

4) Run one job now:

```bash
kubectl --context kind-kind -n ifq create job ifq-download-now --from=cronjob/ifq-download
kubectl --context kind-kind -n ifq logs -f job/ifq-download-now
```
