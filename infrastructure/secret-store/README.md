# secret-store

Cluster-wide `ClusterSecretStore` pointing to Azure Key Vault (`zmoog-homelab-kv`).

ESO uses a Service Principal (`sp-eso-homelab`) with the **Key Vault Secrets User**
role (read-only) to pull secrets into each app namespace.

## Bootstrap (one-time, per cluster)

The SP credentials live in a k8s Secret that is **not** tracked in git.
Apply it once after the cluster is created:

```bash
kubectl create namespace external-secrets

kubectl create secret generic azure-sp-secret \
  --namespace external-secrets \
  --from-literal=client-id=ef66d794-cf75-4cf9-bbd9-c366697d7fac \
  --from-literal=client-secret=<sp-password>
```

The SP password was generated during setup — retrieve it from your password manager.

## Azure resources

| Resource        | Value                                      |
|-----------------|--------------------------------------------|
| Tenant ID       | `5611623b-9128-461e-9d7f-a0d9c270ead2`     |
| Subscription    | `33ebbfb4-db72-4627-b106-f2309739d51f`     |
| Resource Group  | `zmoog-homelab`                            |
| Key Vault       | `zmoog-homelab-kv` (eastus2)               |
| Service Principal | `sp-eso-homelab`                         |
| SP App ID       | `ef66d794-cf75-4cf9-bbd9-c366697d7fac`     |
