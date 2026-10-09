"""Negative tests for deployment attestation binding. No physical security proof."""
import unittest
from hybrid_kernel.attestation import DeploymentAttestation,AttestationError
from hybrid_kernel.deployment import GovernedDeployment,ProductionBlocked
from tcb.canon import digest

class DeploymentAttestationTests(unittest.TestCase):
    def fixture(self,**overrides):
        fields={"release_digest":"sha256:"+"a"*64,"genesis_pin":"sha256:"+"b"*64,
                "ledger_binding":digest("/tmp/db"),"registry_digest":"sha256:"+"c"*64,
                "issued_at":100,"expires_at":200,"assessment_digest":"sha256:"+"d"*64,
                "verifier_id":"independent-assessor"}
        fields.update(overrides)
        return DeploymentAttestation(**fields)
    def check(self, att, **overrides):
        args={"release_digest":"sha256:"+"a"*64,"genesis_pin":"sha256:"+"b"*64,
              "ledger_path":"/tmp/db","registry_digest":"sha256:"+"c"*64,"now":150}
        args.update(overrides)
        return att.validate(**args)
    def test_exact_binding(self):
        self.assertTrue(self.check(self.fixture()))
    def test_wrong_genesis(self):
        with self.assertRaises(AttestationError):self.check(self.fixture(),genesis_pin="sha256:"+"e"*64)
    def test_wrong_ledger(self):
        with self.assertRaises(AttestationError):self.check(self.fixture(),ledger_path="/tmp/other")
    def test_wrong_registry(self):
        with self.assertRaises(AttestationError):self.check(self.fixture(),registry_digest="sha256:"+"f"*64)
    def test_expired(self):
        with self.assertRaises(AttestationError):self.check(self.fixture(),now=200)
    def test_future(self):
        with self.assertRaises(AttestationError):self.check(self.fixture(),now=99)
    def test_boolean_cannot_bypass(self):
        with self.assertRaises(TypeError):
            GovernedDeployment(ledger_path="/tmp/db",pin_store=None,
                               genesis_pin="sha256:"+"b"*64,registry=None,
                               attested_now=150,physical_enforcement_confirmed=True)
if __name__=="__main__":unittest.main()
