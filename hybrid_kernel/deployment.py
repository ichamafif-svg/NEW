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
                 deployment_attestation=None,trusted_now=None):
        if not callable(trusted_now):
            raise ProductionBlocked("TRUST.CLOCK_REQUIRED")
        if not isinstance(registry,CapabilityRegistry):
            raise ProductionBlocked("TRUST.NO_REGISTRY")
        if not isinstance(deployment_attestation,DeploymentAttestation):
            raise ProductionBlocked("TRUST.ATTESTATION_REQUIRED")
        self._registry,self._attestation,self._trusted_now=registry,deployment_attestation,trusted_now
        self._release,self._genesis=code_digest(),genesis_pin
        self._ledger_path=ledger_path
        self._last_at=-1
        if self._check()!=attested_now:
            raise ProductionBlocked("TRUST.CLOCK_MISMATCH")
        self._runtime=ConstitutionalRuntime(ledger_path=ledger_path,pin_store=pin_store,
                                           genesis_pin=genesis_pin)

    def _check(self):
        try:
            now=self._trusted_now()
        except Exception as e:
            raise ProductionBlocked("TRUST.CLOCK_UNAVAILABLE") from e
        if type(now) is not int or now<self._last_at:
            raise ProductionBlocked("TRUST.CLOCK_ROLLBACK")
        self._last_at=now
        if code_digest()!=self._release:
            raise ProductionBlocked("TRUST.RELEASE_CHANGED")
        try:self._registry.validate(now)
        except ContractError as e:raise ProductionBlocked("TRUST.UNVERIFIED:"+str(e)) from e
        try:
            self._attestation.validate(
                release_digest=self._release,genesis_pin=self._genesis,
                ledger_path=self._ledger_path,registry_digest=registry_fingerprint(self._registry),
                now=now)
        except AttestationError as e:
            raise ProductionBlocked("TRUST.ATTESTATION_INVALID") from e
        # WARNING: arbitrary construction of DeploymentAttestation is NOT
        # trustworthy. Callers must be confined to an authenticated attestation
        # verifier/operational boundary; no public endpoint may accept this as
        # raw caller-supplied object.
        return now

    def admit(self,envelope):
        self._check()
        return self._runtime.admit(envelope,validity_check=self._check)
    def snapshot(self):
        self._check()
        return self._runtime.snapshot()
    def health(self,*,required_at=None):
        now=self._check()
        return self._runtime.health(required_at=max(now,required_at or now))
    def guard(self,*,identity,signer,operation_handlers):
        self._check()
        return self._runtime.guard(identity=identity,signer=signer,
                                   operation_handlers=operation_handlers,validity_check=self._check)
    def close(self):return self._runtime.close()
    def __enter__(self):return self
    def __exit__(self,*_):self.close()
