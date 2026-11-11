"""Offline chart rendering checks; no cluster or credentials required."""

from pathlib import Path
import subprocess
import tempfile
import unittest

import yaml


APP = Path(__file__).resolve().parents[1]
CHART = APP / "chart"
REPO = APP.parents[1]
USER_ID = "123456789012345678"


def render(overrides=None, homelab=True, expect_success=True):
    with tempfile.TemporaryDirectory() as directory:
        values = Path(directory) / "values.yaml"
        values.write_text(yaml.safe_dump(overrides or {}))
        command = ["helm", "template", "hermes", str(CHART), "--namespace", "hermes"]
        if homelab:
            command += ["-f", str(CHART / "values-homelab-kind.yaml")]
        command += ["-f", str(values)]
        result = subprocess.run(command, text=True, capture_output=True, check=False)
    if not expect_success:
        return result
    if result.returncode:
        raise AssertionError(result.stderr)
    return {item["kind"]: item for item in yaml.safe_load_all(result.stdout) if item}


def container(documents):
    return documents["Deployment"]["spec"]["template"]["spec"]["containers"][0]


def environment(documents):
    return {item["name"]: item for item in container(documents)["env"]}


class ChartTests(unittest.TestCase):
    def test_bootstrap_is_base_default_and_does_not_need_a_discord_secret(self):
        self.assertEqual(container(render(homelab=False))["args"], ["sleep", "infinity"])
        documents = render({"mode": "bootstrap"})
        self.assertEqual(set(documents), {"Deployment", "PersistentVolumeClaim", "ExternalSecret"})
        process = container(documents)
        self.assertEqual(process["args"], ["sleep", "infinity"])
        self.assertNotIn("command", process)  # Keep the official image entrypoint.
        self.assertNotIn("DISCORD_BOT_TOKEN", environment(documents))
        self.assertNotIn("readinessProbe", process)

    def test_homelab_gateway_uses_the_configured_owner(self):
        documents = render()
        self.assertEqual(container(documents)["args"], ["gateway", "run"])
        self.assertEqual(environment(documents)["DISCORD_ALLOWED_USERS"]["value"], "472444297300541461")
        self.assertIn("DISCORD_BOT_TOKEN", environment(documents))

    def test_base_chart_can_use_a_manually_provisioned_secret(self):
        documents = render(homelab=False)
        self.assertNotIn("ExternalSecret", documents)
        gateway = render({"mode": "gateway", "discord": {"allowedUsers": USER_ID}}, homelab=False)
        self.assertNotIn("ExternalSecret", gateway)
        self.assertIn("DISCORD_BOT_TOKEN", environment(gateway))

    def test_gateway_reads_credential_from_secret_and_restricts_users(self):
        documents = render({"mode": "gateway", "discord": {"allowedUsers": USER_ID}})
        process = container(documents)
        self.assertEqual(process["args"], ["gateway", "run"])
        self.assertNotIn("command", process)
        env = environment(documents)
        self.assertEqual(env["DISCORD_ALLOWED_USERS"]["value"], USER_ID)
        self.assertEqual(env["DISCORD_BOT_TOKEN"]["valueFrom"]["secretKeyRef"], {
            "name": "hermes-secrets", "key": "DISCORD_BOT_TOKEN",
        })
        for name in ("DISCORD_ALLOW_ALL_USERS", "GATEWAY_ALLOW_ALL_USERS", "API_SERVER_ENABLED"):
            self.assertEqual(env[name]["value"], "false")
        self.assertEqual(env["DISCORD_REQUIRE_MENTION"]["value"], "true")
        self.assertIn("gateway-default", process["readinessProbe"]["exec"]["command"][-1])
        self.assertNotIn("livenessProbe", process)

    def test_user_and_free_response_channel_csv_remain_strings(self):
        users = USER_ID + ",234567890123456789"
        documents = render({"mode": "gateway", "discord": {
            "allowedUsers": users, "freeResponseChannels": "345678901234567890",
        }})
        self.assertEqual(environment(documents)["DISCORD_ALLOWED_USERS"]["value"], users)
        self.assertEqual(environment(documents)["DISCORD_FREE_RESPONSE_CHANNELS"]["value"], "345678901234567890")

    def test_state_is_writable_persistent_and_protected(self):
        documents = render()
        pvc = documents["PersistentVolumeClaim"]
        self.assertEqual(pvc["spec"]["storageClassName"], "standard")
        self.assertEqual(pvc["metadata"]["annotations"], {
            "helm.sh/resource-policy": "keep",
            "argocd.argoproj.io/sync-options": "Prune=false,Delete=false",
        })
        self.assertEqual(container(documents)["volumeMounts"], [{"name": "data", "mountPath": "/opt/data"}])
        self.assertEqual(documents["Deployment"]["spec"]["template"]["spec"]["volumes"], [{
            "name": "data", "persistentVolumeClaim": {"claimName": "hermes-data"},
        }])

    def test_single_arm64_agent_has_no_cluster_credentials_or_host_mounts(self):
        documents = render()
        deployment = documents["Deployment"]["spec"]
        self.assertEqual(deployment["replicas"], 1)
        self.assertEqual(deployment["strategy"], {"type": "Recreate"})
        pod = deployment["template"]["spec"]
        self.assertFalse(pod["automountServiceAccountToken"])
        self.assertEqual(pod["nodeSelector"], {"kubernetes.io/os": "linux", "kubernetes.io/arch": "arm64"})
        self.assertFalse(container(documents)["securityContext"]["allowPrivilegeEscalation"])
        self.assertNotIn("ports", container(documents))
        self.assertNotIn("hostNetwork", pod)
        self.assertTrue(all("hostPath" not in volume for volume in pod["volumes"]))
        self.assertIn("@sha256:", container(documents)["image"])
        self.assertIn("memory", container(documents)["resources"]["limits"])
        self.assertEqual(environment(documents)["TERMINAL_ENV"]["value"], "local")

    def test_secret_uses_existing_store_but_not_looters_token(self):
        secret = render()["ExternalSecret"]["spec"]
        self.assertEqual(secret["secretStoreRef"], {"name": "azure-kv", "kind": "ClusterSecretStore"})
        self.assertEqual(secret["target"]["name"], "hermes-secrets")
        self.assertEqual(secret["data"], [{
            "secretKey": "DISCORD_BOT_TOKEN", "remoteRef": {"key": "hermes-discord-bot-token"},
        }])

    def test_invalid_or_unsafe_values_fail_rendering(self):
        cases = [
            {"mode": "gateway", "discord": {"allowedUsers": ""}},
            {"mode": "gateway", "discord": {"allowedUsers": "YOUR_ID"}},
            {"discord": {"allowedUsers": 123456789012345678}},
            {"discord": {"allowedUsers": "123, 456"}},
            {"discord": {"freeResponseChannels": "*"}},
            {"mode": "gatway"},
            {"replicaCount": 2},
            {"image": {"digest": ""}},
            {"image": {"digest": "sha256:bad"}},
            {"mode": "gateway", "discord": {"allowedUser": USER_ID}},
        ]
        for values in cases:
            with self.subTest(values=values):
                result = render(values, expect_success=False)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("schema", result.stderr.lower())

    def test_argo_application_uses_the_homelab_chart_and_namespace(self):
        application = yaml.safe_load((REPO / "clusters/homelab-kind/applications/hermes.yaml").read_text())
        source = application["spec"]["source"]
        self.assertEqual(source["targetRevision"], "main")
        self.assertEqual(source["path"], "apps/hermes/chart")
        self.assertEqual(source["helm"]["valueFiles"], ["values-homelab-kind.yaml"])
        self.assertEqual(application["spec"]["destination"]["namespace"], "hermes")


if __name__ == "__main__":
    unittest.main()
