"""T09: uncertain sends are never repeated, and acknowledgments need signed readback."""
import base64
import sys
import tempfile
import unittest
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from hybrid_kernel.delivery import EscalationOutbox, DeliveryError, PREFIX
from hybrid_kernel.assessment import PREFIX as ASSESSMENT_PREFIX, SignedAssessmentBoundary
from hybrid_kernel.attestation import DeploymentAttestation, registry_fingerprint
from hybrid_kernel.deployment import GovernedDeployment
from hybrid_kernel.externals import Capability, CapabilityRegistry, Status
from tcb.canon import canon, digest
from tcb.release import code_digest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixture import World, T0, DAY


class Transport:
    def __init__(self):
        self.sent, self.receipt = [], None

    def send(self, key, payload):
        self.sent.append((key, payload))
        raise ConnectionError("ACK lost after send")

    def readback(self, key):
        return self.receipt


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "outbox.db"
        self.key = Ed25519PrivateKey.from_private_bytes(b"\x09" * 32)
        self.keys = {"provider": self.key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)}
        self.transport = Transport()
        self.verdict = {"state": "ESCALATED", "current": True, "size": 3,
                        "head": digest("head"), "escalated": [{"obligation": "gap:one",
                        "opened": 100, "due": 120, "escalated_to": ["alice", "bob"]}]}
        self.live = lambda: 150

    def outbox(self, create=False, validity_check=None):
        return EscalationOutbox(self.path, transport=self.transport, provider_keys=self.keys,
                                health_reader=lambda: self.verdict, genesis=digest("genesis"),
                                validity_check=validity_check or self.live, create=create)

    def receipt(self, key, payload):
        claim = {"key": key, "payload_digest": digest(payload),
                 "recipients_digest": digest(payload["recipients"]),
                 "provider": "provider", "delivered_at": 151}
        return {"claim": claim, "signature": base64.b64encode(
            self.key.sign(PREFIX + canon(claim))).decode()}

    def test_lost_ack_restarts_into_readback_without_second_send(self):
        outbox = self.outbox(create=True)
        key, = outbox.enqueue()
        self.assertEqual(outbox.enqueue(), [key])
        self.assertEqual(outbox.deliver(key), "UNKNOWN")
        self.assertEqual(outbox.status(key)["state"], "attempted")
        reopened = self.outbox()
        self.assertEqual(reopened.deliver(key), "UNKNOWN")
        self.assertEqual(len(self.transport.sent), 1)
        self.transport.receipt = self.receipt(*self.transport.sent[0])
        self.assertEqual(reopened.deliver(key), "delivered")
        self.assertEqual(reopened.status(key)["receipt"], self.transport.receipt)
        self.assertEqual(len(self.transport.sent), 1)

    def test_tampered_receipt_cannot_close_delivery(self):
        outbox = self.outbox(create=True)
        key, = outbox.enqueue()
        outbox.deliver(key)
        receipt = self.receipt(*self.transport.sent[0])
        receipt["claim"]["recipients_digest"] = digest(["mallory"])
        self.transport.receipt = receipt
        self.assertEqual(outbox.deliver(key), "UNKNOWN")
        self.assertEqual(outbox.status(key)["state"], "attempted")

    def test_expired_trust_after_durable_attempt_never_sends(self):
        outbox = self.outbox(create=True, validity_check=lambda: 150)
        key, = outbox.enqueue()

        def expired():
            raise RuntimeError("assessment expired")

        outbox.validity_check = expired
        with self.assertRaises(RuntimeError): outbox.deliver(key)
        self.assertEqual(outbox.status(key)["state"], "attempted")
        outbox.validity_check = self.live
        self.assertEqual(outbox.deliver(key), "UNKNOWN")
        self.assertEqual(self.transport.sent, [])

    def test_fault_health_and_missing_outbox_refused(self):
        with self.assertRaises(DeliveryError): self.outbox()
        outbox = self.outbox(create=True)
        self.verdict = {"state": "FAULT"}
        with self.assertRaises(DeliveryError): outbox.enqueue()

    def test_deployment_outbox_reads_actual_escalated_journal(self):
        world = World(tmp=self.tmp.name)
        now = T0 + 10 * DAY
        registry = CapabilityRegistry([
            Capability(f"T{i:02}", f"provider-{i}", f"domain-{i}", "1",
                       digest(i), Status.VERIFIED, now + DAY, T0)
            for i in range(1, 10)
        ])
        private = Ed25519PrivateKey.from_private_bytes(b"\x07" * 32)
        assessor_key = private.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
        attestation = DeploymentAttestation(code_digest(), world.state["domain"],
            digest(str(world.path)), registry_fingerprint(registry), T0, now + DAY,
            digest("assessment-report"), "assessor")
        payload = {"schema": "standard.t-assessment/v1", "assessor_id": "assessor",
                   "attestation": vars(attestation),
                   "capabilities": [{**vars(c), "status": c.status.value} for c in registry.inventory()]}
        bundle = {"payload": payload, "signature": base64.b64encode(
            private.sign(ASSESSMENT_PREFIX + canon(payload))).decode()}
        with GovernedDeployment(ledger_path=world.path, pin_store=world.pins,
            genesis_pin=world.state["domain"], trusted_now=lambda: now,
            trust_boundary=SignedAssessmentBoundary(bundle, {"assessor": assessor_key})) as deployed:
            outbox = EscalationOutbox(self.path, transport=self.transport,
                provider_keys=self.keys, health_reader=deployed.health,
                genesis=world.state["domain"], validity_check=self.live, create=True)
            ids = outbox.enqueue()
            self.assertTrue(ids)
            self.assertTrue(all(outbox.status(key)["state"] == "pending" for key in ids))


if __name__ == "__main__": unittest.main()
