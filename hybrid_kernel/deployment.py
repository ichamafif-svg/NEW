"""Strict deployment facade: externally assessed trust contracts are required.

This facade intentionally does not bootstrap a genesis, create secrets or grant
a runtime effect entitlement. The operator provisions a trusted physical
environment and independently verified evidence for all required contracts.
"""
from __future__ import annotations
from .runtime import ConstitutionalRuntime,IntegrationError
from .externals import CapabilityRegistry,ContractError,CONTRACTS

class ProductionBlocked(RuntimeError):
    pass

class GovernedDeployment:
    """Guarded entry point; NOT a production attestation authority.\n\n    Deployment callers are trusted operators. There is no secure public method\n    to set physical_enforcement_confirmed using an arbitrary boolean.\n    """

    def __init__(self,*,ledger_path,pin_store,genesis_pin,registry,attested_now,
                 physical_enforcement_confirmed=False):
        if not isinstance(registry,CapabilityRegistry):
            raise ProductionBlocked("TRUST.NO_REGISTRY")
        try:registry.validate(attested_now)
        except ContractError as e:raise ProductionBlocked("TRUST.UNVERIFIED:"+str(e)) from e
        if physical_enforcement_confirmed is not True:
            raise ProductionBlocked("TRUST.PHYSICAL_ATTESTATION_REQUIRED")
        # Boolean physical_enforcement_confirmed is operator-controlled and
        # cannot be treated as cryptographic proof of isolation. Do not expose
        # this as an internet-facing production API absent an external attestor.
        self._runtime=ConstitutionalRuntime(ledger_path=ledger_path,pin_store=pin_store,
                                           genesis_pin=genesis_pin)

    def admit(self,envelope):return self._runtime.admit(envelope)
    def snapshot(self):return self._runtime.snapshot()
    def health(self,*,required_at=None):return self._runtime.health(required_at=required_at)
    def guard(self,*,identity,signer,operation_handlers):
        return self._runtime.guard(identity=identity,signer=signer,
                                   operation_handlers=operation_handlers)
    def close(self):return self._runtime.close()
    def __enter__(self):return self
    def __exit__(self,*_):self.close()
