"""T03 fresh time from independently provisioned signing witnesses.

The witness keys and fetch transport must be protected outside the agent. A
fresh random challenge prevents replay. K consumes one integer timestamp; a
nonzero uncertainty interval would need distinct lower and upper bound checks
for delays and expirations, so this adapter requires agreement on exact time.
"""
from __future__ import annotations

import base64
import os

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from tcb.canon import canon

PREFIX = b"standard:time-witness:v1\x00"


class ClockError(ValueError):
    pass


class WitnessClock:
    """A callable T03 clock suitable for GovernedDeployment.trusted_now."""

    def __init__(self, *, genesis, public_keys, quorum, max_skew_ms, fetch):
        if (not isinstance(genesis, str) or not genesis or
                not isinstance(public_keys, dict) or len(public_keys) < 2 or
                any(not isinstance(k, str) or not isinstance(v, bytes) or len(v) != 32
                    for k, v in public_keys.items()) or
                type(quorum) is not int or quorum < 2 or quorum > len(public_keys) or
                type(max_skew_ms) is not int or max_skew_ms != 0 or not callable(fetch)):
            raise ClockError("TIME.CONFIGURATION")
        self.genesis, self.keys, self.quorum = genesis, dict(public_keys), quorum
        self.max_skew_ms, self.fetch, self.last = max_skew_ms, fetch, -1

    def __call__(self):
        nonce = base64.b64encode(os.urandom(24)).decode()
        try:
            quotes = self.fetch(nonce)
        except Exception as exc:
            raise ClockError("TIME.UNAVAILABLE") from exc
        if not isinstance(quotes, list) or len(quotes) > len(self.keys) or len(quotes) < self.quorum:
            raise ClockError("TIME.QUORUM")
        seen, times = set(), []
        for quote in quotes:
            if not isinstance(quote, dict) or set(quote) != {"claim", "signature"}:
                raise ClockError("TIME.QUOTE")
            claim = quote["claim"]
            if not isinstance(claim, dict) or set(claim) != {"genesis", "nonce", "witness", "at"}:
                raise ClockError("TIME.CLAIM")
            witness = claim["witness"]
            key = self.keys.get(witness)
            if (key is None or witness in seen or claim["genesis"] != self.genesis or
                    claim["nonce"] != nonce or type(claim["at"]) is not int or claim["at"] < 0):
                raise ClockError("TIME.BINDING")
            seen.add(witness)
            try:
                if not isinstance(quote["signature"], str) or len(quote["signature"]) > 128:
                    raise ClockError("TIME.SIGNATURE")
                signature = base64.b64decode(quote["signature"], validate=True)
                if len(signature) != 64: raise ClockError("TIME.SIGNATURE")
                Ed25519PublicKey.from_public_bytes(key).verify(signature, PREFIX + canon(claim))
            except (InvalidSignature, ValueError, TypeError) as exc:
                raise ClockError("TIME.SIGNATURE") from exc
            times.append(claim["at"])
        if max(times) - min(times) > self.max_skew_ms or min(times) < self.last:
            raise ClockError("TIME.SKEW_OR_ROLLBACK")
        self.last = min(times)
        return self.last
