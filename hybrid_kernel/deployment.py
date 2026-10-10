"""Strict deployment facade: externally assessed trust contracts are required.

This facade intentionally does not bootstrap a genesis, create secrets or grant
a runtime effect entitlement. The operator provisions a trusted physical
environment and independently verified evidence for all required contracts.
"""
from __future__ import annotations
from .runtime import ConstitutionalRuntime,IntegrationError
from .externals import ContractError
from .attestation import AttestationError,registry_fingerprint
from .assessment import verify_assessment
from .delivery import EscalationOutbox
from tcb.release import code_digest

class ProductionBlocked(RuntimeError):
    pass

class GovernedDeployment:
    """Guarded entry point; NOT a production attestation authority.

    The deployment attestation must originate in an independent trusted verifier,
    not from user-controlled data or an agent-side constructor.
    """

    def __init__(self,*,ledger_path,pin_store,genesis_pin,attested_now,
                 signed_assessment=None,pinned_assessors=None,trusted_now=None,
                 registry=None,deployment_attestation=None):
        if not callable(trusted_now):
            raise ProductionBlocked("TRUST.CLOCK_REQUIRED")
        if registry is not None or deployment_attestation is not None:
            raise ProductionBlocked("TRUST.UNSIGNED_DECLARATION")
        if signed_assessment is None or pinned_assessors is None:
            raise ProductionBlocked("TRUST.SIGNED_ASSESSMENT_REQUIRED")
        try:
            installation=verify_assessment(signed_assessment,pinned_assessors=pinned_assessors,
                release_digest=code_digest(),genesis_pin=genesis_pin,
                ledger_path=ledger_path,now=attested_now)
        except AttestationError as e:
            raise ProductionBlocked("TRUST.ASSESSMENT_INVALID") from e
        registry,deployment_attestation=installation.registry,installation.attestation
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
    def outbox(self,*,path,transport,provider_keys,create=False):
        self._check()
        return EscalationOutbox(path,transport=transport,provider_keys=provider_keys,
            health_reader=lambda:self.health(),genesis=self._genesis,
            validity_check=self._check,create=create)
    def close(self):return self._runtime.close()
    def __enter__(self):return self
    def __exit__(self,*_):self.close()
