# home-telemetry-collector

Collector for home telemetry and personal metrics:
- solar/energy (`zcsazzurro`)
- floor heating/cooling (`wavinsentio`)
- Shelly cloud devices (`shellycloud`)
- time tracking (`toggltrack`)

## Secrets

Create from example and apply to `home-telemetry` namespace:

```bash
cp apps/home-telemetry-collector/secrets/collector-secret.example.yaml apps/home-telemetry-collector/secrets/collector-secret.yaml
# edit values, then:
kubectl apply -n home-telemetry -f apps/home-telemetry-collector/secrets/collector-secret.yaml
```

## Deploy manually (Helm)

```bash
helm upgrade --install home-telemetry-collector apps/home-telemetry-collector/chart \
  --namespace home-telemetry \
  --create-namespace \
  -f apps/home-telemetry-collector/chart/values-homelab-kind.yaml
```
