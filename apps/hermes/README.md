# Hermes Agent (Discord)

Hermes on the existing ARM64 `homelab-kind` cluster, using ChatGPT/Codex
subscription sign-in and a separate Discord bot. No Service, Ingress, public
port, host Docker socket, or Kubernetes API token is needed.

## Deployment model

**Current homelab configuration:** gateway mode is enabled after successful
ChatGPT/Codex authentication and minimal local tool setup. The base chart still
defaults to bootstrap for fresh installations; the staged instructions below
explain that initial setup. Do not copy the active homelab override onto a fresh,
unauthenticated data volume without first setting `mode: bootstrap`.

- Official `nousresearch/hermes-agent:v0.23.1`, pinned to a multi-architecture
  digest verified to include `linux/arm64`. The chart targets ARM64 Linux nodes.
- One replica with `Recreate` updates; `/opt/data` is a writable `standard` PVC.
- **`mode: bootstrap` by default:** the image initializes and runs `sleep infinity`
  so you can authenticate interactively before starting the bot.
- `mode: gateway` runs `gateway run` through the image's original s6 entrypoint.
- External Secrets pulls `hermes-discord-bot-token` from `ClusterSecretStore/azure-kv`
  into `hermes-secrets`, key `DISCORD_BOT_TOKEN`.
- A numeric user allowlist is mandatory in gateway mode. Mentions are required in
  server channels by default; DMs do not require a mention.
- ChatGPT's refreshable OAuth state stays on the PVC, **not in Git or a read-only
  Secret mount**. Do not have External Secrets overwrite it periodically.

ChatGPT Plus includes first-party Codex access; Hermes offers its own
ChatGPT/Codex OAuth integration. Hermes does not document exact plan eligibility
or quota accounting for third-party use. This is not unlimited generic API
access. Selecting the ordinary OpenAI API-key provider uses separate API billing.
Other tools may need separate credentials.

## 1. Preview before deployment

From the repository root:

```bash
helm lint apps/hermes/chart -f apps/hermes/chart/values-homelab-kind.yaml
helm template hermes apps/hermes/chart --namespace hermes \
  -f apps/hermes/chart/values-homelab-kind.yaml
```

The Argo root watches `clusters/homelab-kind/applications` on **main** with
automatic sync. **Merging this application deploys the bootstrap pod**, creates
its PVC, and asks ESO to fetch the Discord token. Do not merge before reviewing
resources, storage, and the secret reference. If the vault entry is absent, ESO
will report an error, but the bootstrap container deliberately does not depend
on the Kubernetes Secret.

No cluster recreation or manual application of rendered Helm manifests is
required. Keep subsequent configuration changes in Git so Argo self-healing does
not undo imperative patches.

## 2. Create a dedicated Discord bot and vault secret

Use a **different Discord application/token from looter**, which already uses
`discord-bot-token`. Do not reset or reuse Looter's credential.

1. Open <https://discord.com/developers/applications>, create an application, and
   visit its **Bot** page.
2. Enable **Message Content Intent** and **Server Members Intent** as required by
   the Hermes Discord guide. Leave **Require OAuth2 Code Grant** disabled.
3. Generate/copy the bot token privately. Never put it in Helm values, Git,
   terminal command arguments/history, screenshots, or chat.
4. In the Azure portal, open Key Vault **zmoog-homelab-kv → Secrets →
   Generate/Import**. Create **hermes-discord-bot-token** with that token as its
   value. You need vault write permission; ESO's read-only service principal
   does not provide it.
5. In Discord, enable **Settings → Advanced → Developer Mode**, then right-click
   your own user and **Copy User ID**. This ID is public configuration, not a
   token. Put it in `values-homelab-kind.yaml` as a **quoted string**:

   ```yaml
   mode: bootstrap
   discord:
     allowedUsers: "123456789012345678"  # replace with your own ID
   externalSecret:
     enabled: true
   ```

6. Invite the bot with OAuth2 scopes `bot` and `applications.commands`. Use
   channel-scoped permissions, not Administrator: View Channels, Send Messages,
   Embed Links, Attach Files, Read Message History, Create Public Threads, Send
   Messages in Threads, and Add Reactions. A manual invite URL (replace the
   application ID) is:

   ```text
   https://discord.com/oauth2/authorize?client_id=YOUR_APPLICATION_ID&scope=bot+applications.commands&permissions=309237763136
   ```

A private test server/channel is a good starting point. The bot remains offline
until gateway mode is enabled. Only users on `discord.allowedUsers` should be
able to invoke it. Keep allow-all flags off. Avoid channel-based authorization
or role-based access for this personal trial.

## 3. Sync bootstrap and protect the data

After review/merge and Argo sync, run on the Pi:

```bash
kubectl --context kind-homelab-kind -n hermes rollout status deployment/hermes --timeout=300s
kubectl --context kind-homelab-kind -n hermes get pvc
kubectl --context kind-homelab-kind -n hermes get externalsecret
kubectl --context kind-homelab-kind -n hermes wait \
  --for=condition=Ready externalsecret/hermes-secrets --timeout=120s
```

The image's ARM64 layer sizes sum to approximately **1.03 GiB compressed**;
allow additional room for unpacking, temporary pull data, workspace and logs.
The Pi had 14 GiB free on SD and 4.4 GiB available RAM when checked. Requests and
limits are starting estimates, not measured Hermes requirements.

The PVC has Helm keep and Argo `Prune=false,Delete=false` annotations. These
protect against normal automated cleanup, **not direct PVC/namespace deletion**.
The existing StorageClass has reclaim policy `Delete`. After the claim binds,
change only its PV to `Retain`:

```bash
PV="$(kubectl --context kind-homelab-kind -n hermes get pvc hermes-data \
  -o jsonpath='{.spec.volumeName}')"
test -n "$PV" && kubectl --context kind-homelab-kind patch pv "$PV" \
  --type=merge -p '{"spec":{"persistentVolumeReclaimPolicy":"Retain"}}'
```

Do not change the global StorageClass. Local-path data is inside the kind node's
`/var` Docker volume, not an independently managed host bind mount. Retain is not
protection against removing that Docker volume, kind cluster deletion, SD-card
failure, or volume pruning. Back up off the Pi before any such operations.
`persistence.size: 2Gi` is **not a hard quota** with this provisioner.

## 4. Authenticate with your ChatGPT subscription

Run the interactive provider picker in the bootstrap pod:

```bash
kubectl --context kind-homelab-kind -n hermes exec -it deployment/hermes -- hermes model
```

Choose **ChatGPT or Codex Subscription** (provider `openai-codex`), open its
provided device-login URL on your laptop, approve with your Plus account, and
select an available model. Do not choose OpenAI API key if you intend to use the
subscription. Device-code login may need enabling in ChatGPT security settings.
Do not install Codex CLI or copy browser cookies for this flow. If device login
is unavailable, see the upstream OAuth guide for the loopback/tunnel alternative.

Keep tool execution inside the pod and its writable workspace:

```bash
kubectl --context kind-homelab-kind -n hermes exec deployment/hermes -- \
  hermes config set terminal.backend local
kubectl --context kind-homelab-kind -n hermes exec deployment/hermes -- \
  hermes config set terminal.cwd /opt/data/workspace
kubectl --context kind-homelab-kind -n hermes exec -it deployment/hermes -- hermes tools
```

In the tool picker, begin with just the file/terminal tools you need. Leave
browser/computer-use and additional integrations disabled for the first trial.
The image creates `/opt/data/workspace` during initialization. Avoid mounting
extra host paths or adding cloud credentials to the agent.

Do not run `hermes gateway setup/start` in bootstrap mode: that can persist
supervised gateway autostart intent, bypassing this staged rollout. Discord's
credentials and allowlist are already supplied declaratively by this chart.

## 5. Enable Discord

Change **only after successful provider authentication and ESO readiness**:

```yaml
# apps/hermes/chart/values-homelab-kind.yaml
mode: gateway
discord:
  allowedUsers: "123456789012345678"  # your actual Discord user ID
externalSecret:
  enabled: true
```

Preview with the same `helm lint` / `helm template` commands, then review/merge.
Argo recreates the pod with the same PVC and starts the gateway. Schema
validation rejects gateway mode without a numeric user allowlist.

```bash
kubectl --context kind-homelab-kind -n hermes rollout status deployment/hermes --timeout=300s
kubectl --context kind-homelab-kind -n hermes logs deployment/hermes --tail=100
```

Send a DM, or `@mention` the bot in its allowed channel. Start with a simple
question, then one harmless workspace file operation. Confirm an unallowlisted
account is rejected if you can test with a second account. Do not print tokens
or auth files when checking logs/configuration.

Gateway readiness checks that s6 reports its default gateway process **up**;
it does not prove a successful Discord login or OpenAI request. There is no
cloud-dependent liveness probe. s6 restarts a crashed gateway; Kubernetes
restarts a failed container. During provider outages the pod may remain Ready.

An optional mention-free channel can be set with quoted numeric IDs:

```yaml
discord:
  allowedUsers: "123456789012345678"
  freeResponseChannels: "234567890123456789"
```

Do not scale beyond one replica. The image starts s6 as root to initialize and
chown its state, then drops the actual agent to UID/GID 10000. The chart retains
that contract and disables privilege escalation, raw networking and Kubernetes
ServiceAccount token automount, but is **not** a restricted/non-root image or
an isolation guarantee against prompt injection. Do not grant it unrelated
secrets or access to the Pi host.

## Operation and recovery

- **Token rotation:** update `hermes-discord-bot-token` in the vault, wait for ESO
  reconciliation, then restart the deployment. Secret-backed environment values
  do not update in existing processes.
- **Re-authentication:** prefer stopping the gateway before changing its auth.
  `kubectl ... exec -it deployment/hermes -- hermes model` uses the same writable
  PVC. Changing models/authentication does not require committing secrets.
- **Return to bootstrap:** first run `hermes gateway stop` through `kubectl exec`
  to persist stopped intent, then change `mode` in Git. Merely changing to
  `sleep infinity` does not erase the upstream image's saved s6 autostart state.
  Do not use `gateway start` or the TUI in bootstrap if you need it to stay inert.
- **Backups:** stop the gateway first (`hermes gateway stop`) for a consistent
  database snapshot. With a private destination, e.g. `umask 077`, stream a backup
  using `kubectl --context kind-homelab-kind -n hermes exec deployment/hermes --
  tar -C /opt/data -czf - . > "$HOME/hermes-backup.tgz"`. Transfer it off the Pi
  securely. It contains reusable OAuth credentials and may contain the Discord
  token after configuration changes; protect it like a password. Start the
  gateway again only when ready (`hermes gateway start`).
- **Removal:** removing the Argo application/chart is not an instruction to
  delete the PVC. Keep `hermes-data` and its PV until you intentionally retire
  or restore the data. Never run `kind delete cluster` as an uninstall step.
- **SD health:** monitor `df -h /` and `/opt/data` usage. Ephemeral-storage limits
  do not limit PVC growth or the node's image cache. Avoid large downloads and
  browser workloads; add an off-device backup and consider SSD for long-term use.

## Chart checks

Requires Helm and Python with PyYAML installed:

```bash
python3 -m unittest discover -s apps/hermes/tests -v
```

These are rendering/schema tests, not a live Raspberry Pi, Discord, OAuth or
s6-runtime smoke test. See the cluster setup output before choosing different
resource budgets. The chart does not mutate the global storage provisioner.

## Sources

- [Hermes v0.23.1 Docker guide](https://github.com/NousResearch/hermes-agent/blob/v0.23.1/website/docs/user-guide/docker.md)
- [Hermes Discord setup](https://hermes-agent.nousresearch.com/docs/user-guide/messaging/discord)
- [Hermes providers](https://hermes-agent.nousresearch.com/docs/integrations/providers)
- [OpenAI Codex authentication](https://developers.openai.com/codex/auth/)
- [OpenAI Codex pricing](https://developers.openai.com/codex/pricing/)

Image verification (read-only; no image pull or container start):

```bash
docker buildx imagetools inspect nousresearch/hermes-agent:v0.23.1
```

The pinned index digest was checked on 2026-11-11. Updating `image.tag` alone
**does not update the binary**: update and verify `image.digest` too, and update
`Chart.yaml`'s `appVersion` and chart version for the new release.
