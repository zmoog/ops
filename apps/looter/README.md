# looter

Custom OpenTelemetry Collector distro for experimentation.

- Source: <https://github.com/zmoog/looter>
- Image: `ghcr.io/zmoog/looter`

## Discord receiver

The Discord receiver is enabled for `homelab-kind` and requires a Discord bot token in `looter-secrets` as `DISCORD_BOT_TOKEN`.

For `homelab-kind`, the chart creates an ExternalSecret that reads the token from Azure Key Vault key `discord-bot-token`.

Add or update that Key Vault secret with the Azure CLI:

```bash
az keyvault secret set \
  --vault-name zmoog-homelab-kv \
  --name discord-bot-token \
  --value "$DISCORD_BOT_TOKEN"
```

For manual setup, copy and edit the example secret:

```bash
cp apps/looter/secrets/looter-secret.example.yaml apps/looter/secrets/looter-secret.yaml
kubectl --context kind-homelab-kind apply -n looter -f apps/looter/secrets/looter-secret.yaml
```

## homelab-kind

Deployed into the `looter` namespace by Argo CD.

Service endpoints inside the cluster:

- OTLP gRPC: `looter.looter.svc.cluster.local:4317`
- OTLP HTTP: `http://looter.looter.svc.cluster.local:4318`
- Health check: `http://looter.looter.svc.cluster.local:13133/`
- pprof: `http://looter.looter.svc.cluster.local:1777`
- zPages: `http://looter.looter.svc.cluster.local:55679`
