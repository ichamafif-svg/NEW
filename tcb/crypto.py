"""DSSE envelopes over in-toto statements, verified with Ed25519 (machines) or a WebAuthn ES256 assertion (humans).
Nothing here holds a secret or generates a key."""
from __future__ import annotations

import base64
import binascii
import hashlib
import json

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from .canon import CanonError, canon, parse

PAYLOAD_TYPE = "application/vnd.in-toto+json"
STATEMENT_TYPE = "https://in-toto.io/Statement/v1"
PREDICATE_PREFIX = "urn:standard:tcb:1:"
ALGORITHMS = ("ed25519", "webauthn-es256")


class EnvelopeError(ValueError):
    pass


def b64d(text: str) -> bytes:
    try:
        return base64.b64decode(text, validate=True)
    except (binascii.Error, TypeError, ValueError):
        raise EnvelopeError("bad base64") from None


def b64u(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def b64u_enc(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def keyid(public_b64: str) -> str:
    return "sha256:" + hashlib.sha256(b64d(public_b64)).hexdigest()


def pae(payload: bytes) -> bytes:
    kind = PAYLOAD_TYPE.encode()
    return b"DSSEv1 %d %s %d %s" % (len(kind), kind, len(payload), payload)


def subject_name(domain: str, kind: str, rid: str) -> str:
    return f"{domain}/{kind}:{rid}"


def statement(domain: str, kind: str, body: dict) -> dict:
    return {"_type": STATEMENT_TYPE, "predicateType": PREDICATE_PREFIX + kind, "predicate": body,
            "subject": [{"name": subject_name(domain, kind, body["id"]), "digest": {"sha256": hashlib.sha256(canon(body)).hexdigest()}}]}


SIGNATURE = ({"keyid", "sig"}, {"keyid", "sig", "webauthn"})


def canonical_public(alg: str, public_b64: str) -> bool:
    """One key, one encoding: Ed25519 is 32 raw bytes, a passkey is an uncompressed P-256 point on the curve."""
    raw = b64d(public_b64)
    if alg == "ed25519":
        return len(raw) == 32
    try:
        point = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), raw)
    except ValueError:
        return False
    return raw == point.public_bytes(Encoding.X962, PublicFormat.UncompressedPoint)


def open_envelope(envelope) -> tuple[str, dict, bytes, str]:
    """(kind, body, signed message, subject name). The payload must be the canonical encoding of a statement, and the
    envelope a closed shape: no unsigned field, one signature per key, in key order. Its bytes then have one meaning."""
    if (not isinstance(envelope, dict) or set(envelope) != {"payloadType", "payload", "signatures"}
            or envelope["payloadType"] != PAYLOAD_TYPE or not isinstance(envelope["signatures"], list)):
        raise EnvelopeError("not a closed DSSE envelope")
    sigs = envelope["signatures"]
    if (not sigs or not all(isinstance(s, dict) and set(s) in SIGNATURE and isinstance(s["keyid"], str) for s in sigs)
            or [s["keyid"] for s in sigs] != sorted({s["keyid"] for s in sigs})
            or any(set(s.get("webauthn", {"authenticatorData": 0, "clientDataJSON": 0})) != {"authenticatorData", "clientDataJSON"}
                   for s in sigs)):
        raise EnvelopeError("signatures are closed, one per key, in key order")
    payload = b64d(envelope.get("payload", ""))
    try:
        st = parse(payload)
    except CanonError as exc:
        raise EnvelopeError(f"payload: {exc}") from None
    if not isinstance(st, dict) or set(st) != {"_type", "predicateType", "predicate", "subject"} or st["_type"] != STATEMENT_TYPE:
        raise EnvelopeError("not an in-toto statement")
    kind = str(st["predicateType"]).removeprefix(PREDICATE_PREFIX)
    body = st["predicate"]
    if kind == st["predicateType"] or not isinstance(body, dict) or not isinstance(st["subject"], list) or len(st["subject"]) != 1:
        raise EnvelopeError("unknown predicate or subject")
    subject = st["subject"][0]
    if not isinstance(subject, dict) or set(subject) != {"name", "digest"} or not isinstance(subject["name"], str):
        raise EnvelopeError("malformed subject")
    if subject.get("digest") != {"sha256": hashlib.sha256(canon(body)).hexdigest()}:
        raise EnvelopeError("subject digest does not bind the predicate")
    return kind, body, pae(payload), str(subject.get("name"))


def verify(key: dict, message: bytes, signature: dict) -> bool:
    try:
        if key["alg"] == "ed25519":
            Ed25519PublicKey.from_public_bytes(b64d(key["public"])).verify(b64d(signature["sig"]), message)
            return True
        if key["alg"] == "webauthn-es256":
            return _webauthn(key, message, signature)
    except (InvalidSignature, EnvelopeError, ValueError, KeyError, TypeError, AttributeError):
        return False
    return False


def _webauthn(key: dict, message: bytes, signature: dict) -> bool:
    """A passkey signs authenticatorData || sha256(clientDataJSON); the challenge must be sha256(PAE)."""
    w = signature["webauthn"]
    auth, client_json = b64u(w["authenticatorData"]), b64u(w["clientDataJSON"])
    client = json.loads(client_json)
    if client.get("type") != "webauthn.get" or client.get("origin") not in key["origins"]:
        return False
    if client.get("challenge") != b64u_enc(hashlib.sha256(message).digest()):
        return False
    if len(auth) < 37 or auth[:32] != hashlib.sha256(key["rp_id"].encode()).digest() or (auth[32] & 0x05) != 0x05:
        return False                                  # wrong relying party, or user not present and verified
    public = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), b64d(key["public"]))
    public.verify(b64u(signature["sig"]), auth + hashlib.sha256(client_json).digest(), ec.ECDSA(hashes.SHA256()))
    return True
