"""Verify an externally signed assessment of all nine Trusted External contracts.

Assessor public keys must be selected by a trusted installation, never supplied
by an agent or inside the signed bundle. A signature authenticates an assessment,
not the truth of the assessor's physical observations.
"""
from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from tcb.canon import CanonError, canon
from .attestation import DeploymentAttestation, AttestationError, registry_fingerprint
from .externals import Capability, CapabilityRegistry, ContractError, Status

PREFIX = b"standard:trusted-external-assessment:v1\x00"
MAX_ASSESSMENT_BYTES = 65536
ATTEST_FIELDS = frozenset(DeploymentAttestation.__dataclass_fields__)
CAP_FIELDS = frozenset(Capability.__dataclass_fields__)


@dataclass(frozen=True)
class AssessedInstallation:
    registry: CapabilityRegistry
    attestation: DeploymentAttestation
    assessor_id: str


def verify_assessment(bundle, *, pinned_assessors, release_digest, genesis_pin,
                      ledger_path, now) -> AssessedInstallation:
    """Reject unknown fields, unsigned status, wrong binding or stale evidence.

    `pinned_assessors` maps assessor IDs to raw 32-byte Ed25519 public keys.
    The operator must protect this mapping outside the agent's trust domain.
    """
    try:
        if not isinstance(bundle, dict) or set(bundle) != {"payload", "signature"}:
            raise AttestationError("ASSESSMENT.ENVELOPE")
        payload = bundle["payload"]
        raw = canon(payload)
        if len(raw) > MAX_ASSESSMENT_BYTES or not isinstance(payload, dict) or set(payload) != {
            "schema", "assessor_id", "attestation", "capabilities"
        } or payload["schema"] != "standard.t-assessment/v1":
            raise AttestationError("ASSESSMENT.SHAPE")
        assessor_id = payload["assessor_id"]
        if not isinstance(assessor_id, str) or not assessor_id:
            raise AttestationError("ASSESSMENT.ASSESSOR")
        key = pinned_assessors.get(assessor_id)
        if not isinstance(key, bytes) or len(key) != 32:
            raise AttestationError("ASSESSMENT.UNTRUSTED_ASSESSOR")
        signature = base64.b64decode(bundle["signature"], validate=True)
        if len(signature) != 64:
            raise AttestationError("ASSESSMENT.SIGNATURE_SIZE")
        Ed25519PublicKey.from_public_bytes(key).verify(signature, PREFIX + raw)
        att_raw = payload["attestation"]
        if not isinstance(att_raw, dict) or set(att_raw) != ATTEST_FIELDS:
            raise AttestationError("ASSESSMENT.ATTESTATION_SHAPE")
        if att_raw["verifier_id"] != assessor_id:
            raise AttestationError("ASSESSMENT.VERIFIER")
        cap_raw = payload["capabilities"]
        if not isinstance(cap_raw, list) or len(cap_raw) != 9 or any(
            not isinstance(c, dict) or set(c) != CAP_FIELDS for c in cap_raw
        ):
            raise AttestationError("ASSESSMENT.CAPABILITY_SHAPE")
        registry = CapabilityRegistry([
            Capability(**{**c, "status": Status(c["status"])}) for c in cap_raw
        ])
        attestation = DeploymentAttestation(**att_raw)
        registry.validate(now)
        attestation.validate(release_digest=release_digest, genesis_pin=genesis_pin,
                             ledger_path=ledger_path, registry_digest=registry_fingerprint(registry),
                             now=now)
        return AssessedInstallation(registry, attestation, assessor_id)
    except (InvalidSignature, binascii.Error, ValueError, TypeError, KeyError, AttributeError,
            CanonError, ContractError) as exc:
        raise AttestationError("ASSESSMENT.INVALID:" + type(exc).__name__) from None
