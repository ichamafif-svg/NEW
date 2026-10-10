"""A locally fabricated registry cannot enter the deployment boundary."""
import base64
import copy
import unittest

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from hybrid_kernel.assessment import PREFIX, verify_assessment
from hybrid_kernel.attestation import AttestationError, registry_fingerprint
from hybrid_kernel.deployment import GovernedDeployment, ProductionBlocked
from hybrid_kernel.externals import Capability, CapabilityRegistry, Status
from tcb.canon import canon, digest


class AssessmentTests(unittest.TestCase):
    def setUp(self):
        self.private = Ed25519PrivateKey.from_private_bytes(b"\x02" * 32)
        self.keys = {"assessor": self.private.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)}
        registry = CapabilityRegistry([
            Capability(f"T{i:02}", f"provider-{i}", f"domain-{i}", "1", digest(i),
                       Status.VERIFIED, 200, 100) for i in range(1, 10)
        ])
        self.release, self.genesis = digest("release"), digest("genesis")
        self.payload = {
            "schema": "standard.t-assessment/v1", "assessor_id": "assessor",
            "attestation": {"release_digest": self.release, "genesis_pin": self.genesis,
                            "ledger_binding": digest("/tmp/ledger"),
                            "registry_digest": registry_fingerprint(registry),
                            "issued_at": 100, "expires_at": 200,
                            "assessment_digest": digest("report"), "verifier_id": "assessor"},
            "capabilities": [{**vars(c), "status": c.status.value} for c in registry.inventory()]}

    def bundle(self, payload=None):
        payload = copy.deepcopy(self.payload if payload is None else payload)
        return {"payload": payload, "signature": base64.b64encode(
            self.private.sign(PREFIX + canon(payload))).decode()}

    def verify(self, bundle, **kwargs):
        args = dict(pinned_assessors=self.keys, release_digest=self.release,
                    genesis_pin=self.genesis, ledger_path="/tmp/ledger", now=150)
        return verify_assessment(bundle, **{**args, **kwargs})

    def test_signed_nine_contracts_are_bound_to_installation(self):
        self.assertTrue(self.verify(self.bundle()).registry.validate(150))

    def test_status_tamper_after_signature_fails(self):
        bundle = self.bundle()
        bundle["payload"]["capabilities"][0]["status"] = "REJECTED"
        with self.assertRaises(AttestationError): self.verify(bundle)

    def test_wrong_pinned_assessor_fails(self):
        with self.assertRaises(AttestationError):
            self.verify(self.bundle(), pinned_assessors={"assessor": b"\x03" * 32})

    def test_signed_payload_still_fails_wrong_release_or_genesis(self):
        for field in ("release_digest", "genesis_pin"):
            with self.subTest(field=field), self.assertRaises(AttestationError):
                self.verify(self.bundle(), **{field: digest("other")})

    def test_signed_missing_contract_fails(self):
        payload = copy.deepcopy(self.payload)
        payload["capabilities"].pop()
        with self.assertRaises(AttestationError): self.verify(self.bundle(payload))

    def test_plain_objects_cannot_open_deployment(self):
        with self.assertRaises(ProductionBlocked):
            GovernedDeployment(ledger_path="/tmp/ledger", pin_store=object(),
                               genesis_pin=self.genesis, attested_now=150,
                               registry=CapabilityRegistry([]), trusted_now=lambda: 150)


if __name__ == "__main__": unittest.main()
