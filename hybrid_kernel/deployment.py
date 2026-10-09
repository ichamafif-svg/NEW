"""Strict deployment facade: externally assessed trust contracts are required.

This facade intentionally does not bootstrap a genesis, create secrets or grant
a runtime effect entitlement. The operator provisions a trusted physical
environment and independently verified evidence for all required contracts.
"""
from __future__ import annotations
from .runtime import ConstitutionalRuntime,IntegrationError
from .externals import CapabilityRegistry,ContractError,CONTRACTS
from .attestation import DeploymentAttestation,AttestationError,registry_fingerprint
from tcb.release import code_digest

class ProductionBlocked(RuntimeError):
    pass

class GovernedDeployment:
    """Guarded entry point; NOT a production attestation authority.

    The deployment attestation must originate in an independent trusted verifier,
    not from user-controlled data or an agent-side constructor.
    """

    def __init__(self,*,ledger_path,pin_store,genesis_pin,registry,attested_now,
                 deployment_attestation=None):
        if not isinstance(registry,CapabilityRegistry):
            raise ProductionBlocked("TRUST.NO_REGISTRY")
        try:registry.validate(attested_now)
        except ContractError as e:raise ProductionBlocked("TRUST.UNVERIFIED:"+str(e)) from e
        if not isinstance(deployment_attestation,DeploymentAttestation):
            raise ProductionBlocked("TRUST.ATTESTATION_REQUIRED")
        try:
            deployment_attestation.validate(
                release_digest=code_digest(),genesis_pin=genesis_pin,
                ledger_path=ledger_path,registry_digest=registry_fingerprint(registry),
                now=attested_now)
        except AttestationError as e:
            raise ProductionBlocked("TRUST.ATTESTATION_INVALID") from e
        # WARNING: arbitrary construction of DeploymentAttestation is NOT
        # trustworthy. Callers must be confined to an authenticated attestation
        # verifier/operational boundary; no public endpoint may accept this as
        # raw caller-supplied object.
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
