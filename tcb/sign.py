"""Producing a signed statement (Ed25519). Used by the guard and by clients; the judge never signs."""
from __future__ import annotations

import base64

from .canon import canon
from .crypto import PAYLOAD_TYPE, pae, statement


def envelope(domain: str, kind: str, body: dict, signers: list) -> dict:
    """signers: [(keyid, Ed25519PrivateKey)]; several signers co-sign the same statement (thresholds)."""
    payload = canon(statement(domain, kind, body))
    message = pae(payload)
    return {"payloadType": PAYLOAD_TYPE, "payload": base64.b64encode(payload).decode(),
            "signatures": [{"keyid": kid, "sig": base64.b64encode(key.sign(message)).decode()}
                           for kid, key in sorted(dict(signers).items())]}
