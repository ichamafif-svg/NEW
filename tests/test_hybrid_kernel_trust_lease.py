"""A deployment trust lease must be live at use, including inside the effect gate."""
import sys
import base64
import unittest
from pathlib import Path
from unittest.mock import patch
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixture import T0, World
from tcb.canon import digest, canon
from tcb.release import code_digest
from hybrid_kernel.attestation import DeploymentAttestation, registry_fingerprint
from hybrid_kernel.deployment import GovernedDeployment, ProductionBlocked
from hybrid_kernel.externals import Capability, CapabilityRegistry, Status
from hybrid_kernel.runtime import ConstitutionalRuntime
from hybrid_kernel.assessment import PREFIX, SignedAssessmentBoundary
from tcb.sign import envelope


def deployment(now, *, expires=200):
    genesis = digest("genesis")
    registry = CapabilityRegistry([
        Capability(f"T{i:02}", "assessed-provider", f"domain-{i}", "1",
                   digest(f"assessment-{i}"), Status.VERIFIED, expires, 100)
        for i in range(1, 10)
    ])
    attestation = DeploymentAttestation(code_digest(), genesis, digest("/tmp/ledger"),
                                        registry_fingerprint(registry), 100, expires,
                                        digest("operator-assessment"), "independent-verifier")
    payload = {"schema": "standard.t-assessment/v1", "assessor_id": "independent-verifier",
               "attestation": vars(attestation),
               "capabilities": [{**vars(c), "status": c.status.value} for c in registry.inventory()]}
    private = Ed25519PrivateKey.from_private_bytes(b"\x11" * 32)
    bundle = {"payload": payload, "signature": base64.b64encode(
        private.sign(PREFIX + canon(payload))).decode()}
    keys = {"independent-verifier": private.public_key().public_bytes(
        Encoding.Raw, PublicFormat.Raw)}
    clock = lambda: now[0]
    with patch("hybrid_kernel.deployment.ConstitutionalRuntime") as runtime:
        instance = GovernedDeployment(ledger_path="/tmp/ledger", pin_store=object(),
                                      genesis_pin=genesis,
                                      trust_boundary=SignedAssessmentBoundary(bundle, keys),
                                      trusted_now=clock)
    return instance, runtime.return_value


class TrustLeaseTests(unittest.TestCase):
    def test_expiry_blocks_existing_instance(self):
        now = [150]
        deployed, runtime = deployment(now)
        deployed.admit({"signed": True})
        now[0] = 200
        with self.assertRaises(ProductionBlocked):
            deployed.admit({"signed": True})
        runtime.admit.assert_called_once()

    def test_expired_lease_does_not_block_signed_restriction(self):
        now = [150]
        deployed, runtime = deployment(now)
        now[0] = 200
        w = World()
        restriction = envelope(digest("genesis"), "freeze",
                               {"id": "freeze-1", "author": "carol", "at": T0 + 1, "scope": "*"},
                               [w.cosigner("carol")])
        deployed.admit(restriction)
        runtime.admit.assert_called_once()

    def test_clock_rollback_blocks_existing_instance(self):
        now = [150]
        deployed, runtime = deployment(now)
        deployed.admit({"signed": True})
        now[0] = 149
        with self.assertRaisesRegex(ProductionBlocked, "CLOCK_ROLLBACK"):
            deployed.admit({"signed": True})
        runtime.admit.assert_called_once()

    def test_admission_checks_trust_inside_write_transaction(self):
        w = World()
        entry, _ = w.signed("freeze", "carol", T0 + 1, scope="*")
        runtime = ConstitutionalRuntime(ledger_path=w.path, pin_store=w.pins,
                                        genesis_pin=w.state["domain"])

        def expired():
            raise ProductionBlocked("TRUST.ATTESTATION_INVALID")

        with self.assertRaises(ProductionBlocked):
            runtime.admit(entry["envelope"], validity_check=expired)
        self.assertEqual(runtime.snapshot()["size"], w.state["size"])
        runtime.close()

    def test_trust_loss_after_reservation_never_dispatches(self):
        w = World()
        grant, t = w.grant("agent", ["effect:merge"], ["repo:pr:*"], T0 + 1)
        intent = w.add("intent", "agent", t, under=grant, op="merge",
                       args={"pr": "42", "method": "squash"})
        sent = []
        guard = w.guard(lambda *args: sent.append(args) or "ok")
        calls = [0]

        def live():
            calls[0] += 1
            if calls[0] == 5:  # issue and reserve each check twice, then check at dispatch
                raise ProductionBlocked("TRUST.ATTESTATION_INVALID")
            return t

        guard.validity_check = live
        guard.issue(intent, t + 1)
        token = w.state["token_of"][intent]
        with self.assertRaises(ProductionBlocked):
            guard.redeem(token, t + 2)
        state = w.journal.snapshot()
        self.assertIn(token, state["reserved"])
        self.assertIn(f"reconcile:{intent}", state["obligations"])
        self.assertNotIn(token, state["executed"])
        self.assertEqual(sent, [])


if __name__ == "__main__":
    unittest.main()
