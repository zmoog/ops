# ops

GitOps repo for personal workloads.

## Structure

- `apps/<name>/chart`: Helm chart for one app
- `apps/<name>/secrets`: local secret templates (`*.example.yaml` tracked)
- `argocd/applications`: Argo CD `Application` manifests

## Current apps

- `ifq`: daily IFQ download CronJob (uploads PDF to Dropbox)
