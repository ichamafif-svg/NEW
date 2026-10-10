"""Agents can see the actual law and gaps, but their view never grants authority."""
import copy
import json
import sys
import tempfile
import unittest
import subprocess
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixture import World, Refused, make_law
from hybrid_kernel.release_gate import ROOT
from maintenance.constitution import ViewError, agent_view
from ops.agent import craft
from ops.cycle import effective_targets
from tcb.canon import digest
from standard.surface import render_m2


class AgentConstitutionTests(unittest.TestCase):
    def setUp(self):
        self.world = World()
        self.state = copy.deepcopy(self.world.state)
        self.health = self.world.journal.health()
        self.readiness = json.loads((ROOT / "release_readiness.json").read_text())

    def tearDown(self):
        self.world.journal.close()

    def view(self, **overrides):
        return agent_view(self.world.kernel, overrides.get("state", self.state),
                          overrides.get("health", self.health), readiness=self.readiness)

    def test_agent_sees_pinned_effective_law_work_and_unqualified_t(self):
        view = self.view()
        self.assertEqual(digest(view["law"]), view["basis"]["law_digest"])
        self.assertEqual(view["basis"]["head"], self.health["head"])
        self.assertIn("remediate-autonomous", view["law"]["conditions"])
        self.assertIn("pr42-ci", {target["id"] for target in view["law"]["targets"]})
        self.assertEqual({g["contract"] for g in view["trust_gaps"]},
                         {f"T{i:02}" for i in range(1, 10)})
        self.assertEqual({g["id"] for g in view["trust_work"]},
                         {f"qualify:T{i:02}" for i in range(1, 10)})
        self.assertTrue(all(g["closure"] == "independent_qualification" for g in view["trust_work"]))
        self.assertEqual(view["work"]["status"], "REVIEW")
        self.assertNotIn("allowed", view)
        view["law"]["conditions"].clear()
        self.assertIn("remediate-autonomous", self.world.kernel.law_of(self.state).release["conditions"])

    def test_law_and_health_cannot_be_assembled_from_different_heads(self):
        stale = copy.deepcopy(self.health)
        stale["head"] = digest("another prefix")
        with self.assertRaises(ViewError): self.view(health=stale)
        broken = copy.deepcopy(self.state)
        broken["law"]["digest"] = digest("another law")
        with self.assertRaises(Refused): self.view(state=broken)

    def test_agent_prompt_receives_law_as_data_without_acquiring_permission(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "requirements.txt").write_text("example==1.0\n")
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            subprocess.run(["git", "add", "requirements.txt"], cwd=repo, check=True)
            captured = []
            with patch("ops.agent.claude", side_effect=lambda prompt, key:
                       captured.append(prompt) or {"title": "repair", "files": {"requirements.txt": "example==2.0\n"}}):
                result = craft(repo, "vulns", "found:1", "unused",
                               constitution=render_m2(self.view(), "vulns"))
            self.assertEqual(result["files"], {"requirements.txt": "example==2.0\n"})
            self.assertIn(self.health["head"], captured[0])
            self.assertIn("remediate-autonomous", captured[0])
            self.assertIn("qualification physique", captured[0])

    def test_detected_secret_is_not_in_model_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            secret = "-----BEGIN PRIVATE KEY-----\nsecret-material\n"
            (repo / "private.txt").write_text(secret)
            (repo / "requirements.txt").write_text("example==1.0\n")
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            subprocess.run(["git", "add", "private.txt", "requirements.txt"], cwd=repo, check=True)
            captured = []
            with patch("ops.agent.claude", side_effect=lambda prompt, key:
                       captured.append(prompt) or {"files": {"requirements.txt": "example==2.0\n"}}):
                craft(repo, "vulns", "found:1", "unused",
                      constitution=render_m2(self.view(), "vulns"))
            self.assertNotIn(secret, captured[0])
            self.assertIn("example==1.0", captured[0])

    def test_demo_supported_probe_reads_client_tightening(self):
        tighter = World(law=make_law(tighten={"targets": {"vulns": {"due_ms": 60_000}}}))
        try:
            node = type("DemoNode", (), {"kernel": tighter.kernel, "state": tighter.state})()
            self.assertEqual(effective_targets(node)["vulns"]["due_ms"], 60_000)
        finally:
            tighter.journal.close()


if __name__ == "__main__": unittest.main()
