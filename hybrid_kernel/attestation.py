"""Fail-closed installation attestation for the Standard runtime.

The operator must supply a separately authenticated, deployment-bound
assessment. This type proves *binding and shape only*, not physical truth.
"""
from __future__ import annotations
from dataclasses import dataclass
from tcb.canon import digest

class AttestationError(ValueError):pass

@dataclass(frozen=True)
class DeploymentAttestation:
    """Already verified by an independent attestation verifier (T01/T02/T04/T07).

    Instantiating this Python object is not a security boundary. The
    verifier's construction of it MUST be inaccessible to untrusted agents.
    """
    release_digest:str
    genesis_pin:str
    ledger_binding:str
    registry_digest:str
    issued_at:int
    expires_at:int
    assessment_digest:str
    verifier_id:str

    def validate(self,*,release_digest,genesis_pin,ledger_path,registry_digest,now):
        checks=(
            self.release_digest==release_digest,
            self.genesis_pin==genesis_pin,
            self.ledger_binding==digest(str(ledger_path)),
            self.registry_digest==registry_digest,
            isinstance(self.assessment_digest,str) and self.assessment_digest.startswith("sha256:"),
            isinstance(self.verifier_id,str) and bool(self.verifier_id),
            type(now) is int and type(self.issued_at) is int and type(self.expires_at) is int,
        )
        if not all(checks) or not self.issued_at<=now<self.expires_at:
            raise AttestationError("TRUST.ATTESTATION_INVALID")
        return True

def registry_fingerprint(registry):
    """Canonical fingerprint of the registered capability declarations.

    This does not prove the authenticity of external assessment evidence.
    """
    return digest([{"contract_id":c.contract_id,"provider_id":c.provider_id,
                    "trust_domain":c.trust_domain,"version":c.version,
                    "evidence_digest":c.evidence_digest,"status":c.status.value,
                    "expires_at":c.expires_at,"verified_at":c.verified_at}
                   for c in registry.inventory()])
