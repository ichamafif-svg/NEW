"""Strict trust-contract and deployment gating regression tests."""
import unittest
from hybrid_kernel.externals import Capability,CapabilityRegistry,ContractError,Status
from hybrid_kernel.deployment import GovernedDeployment,ProductionBlocked

def cap(i,status=Status.VERIFIED,until=9999):
    return Capability(f"T{i:02}","provider","domain","1",
        "sha256:"+"a"*64,status,until,100)

class ExternalContractTests(unittest.TestCase):
    def test_no_trust_catalog_denied(self):
        with self.assertRaises(ProductionBlocked):
            GovernedDeployment(ledger_path="none",pin_store=None,genesis_pin="invalid",
                                registry=None,attested_now=200)
    def test_all_nine_assessments_required(self):
        reg=CapabilityRegistry([cap(i) for i in range(1,9)])
        with self.assertRaises(ContractError):
            reg.validate(200)
    def test_expiry_fails_closed(self):
        reg=CapabilityRegistry([cap(i,until=200 if i==9 else 9999) for i in range(1,10)])
        with self.assertRaises(ContractError):
            reg.validate(200)
    def test_future_assessment_cannot_grant_current_access(self):
        reg=CapabilityRegistry([cap(i) for i in range(1,10)])
        with self.assertRaisesRegex(ContractError,"NOT_YET_VERIFIED"):
            reg.validate(99)
    def test_self_report_unverified_fails_closed(self):
        reg=CapabilityRegistry([cap(i,Status.INDETERMINATE if i==5 else Status.VERIFIED)
                                for i in range(1,10)])
        with self.assertRaises(ContractError):
            reg.validate(200)
    def test_duplicate_contract_rejected(self):
        with self.assertRaises(ContractError):
            CapabilityRegistry([cap(1),cap(1)])
    def test_invalid_time_rejected(self):
        with self.assertRaises(ContractError):
            cap(1,until=100)
    def test_complete_registry_still_requires_physical_validation(self):
        reg=CapabilityRegistry([cap(i) for i in range(1,10)])
        self.assertTrue(reg.validate(200))
        with self.assertRaises(ProductionBlocked):
            GovernedDeployment(ledger_path="none",pin_store=None,genesis_pin="invalid",
                                registry=reg,attested_now=200)
if __name__=="__main__":unittest.main()
