"""Route-specific K/T integration; providers are selected by the installation.

The local Python facade is not isolation. Credentials, keys, storage and ports
must live behind an operator-controlled boundary inaccessible to the agent.
"""
from __future__ import annotations

from tcb.crypto import EnvelopeError, open_envelope
from tcb.release import code_digest
from .core import SHAPES
from .runtime import ConstitutionalRuntime


class ProductionBlocked(RuntimeError):
    pass


# Missing trust stops its dependent operation, not unrelated autonomy.
BASE = frozenset({"T01", "T02", "T04", "T05"})
TIMED = BASE | {"T03"}
EFFECT = TIMED | {"T07", "T08"}
EVIDENCE = {"measurement", "observation", "evidence"}


class GovernedDeployment:
    """Contract boundary. The installation must provision trusted implementations."""

    def __init__(self, *, ledger_path, pin_store, genesis_pin, trust_boundary,
                 trusted_now, effect_port=None, delivery_port=None):
        if not callable(trusted_now) or not callable(getattr(trust_boundary, "check", None)):
            raise ProductionBlocked("TRUST.BOUNDARY_REQUIRED")
        self._boundary, self._trusted_now = trust_boundary, trusted_now
        self._effect, self._delivery = effect_port, delivery_port
        self._release, self._genesis, self._ledger_path = code_digest(), genesis_pin, str(ledger_path)
        self._last_at = -1
        self._check(BASE)
        self._runtime = ConstitutionalRuntime(ledger_path=ledger_path,
                                               pin_store=pin_store, genesis_pin=genesis_pin)

    def _check(self, required):
        required = frozenset(required)
        if "T03" in required:
            try: now = self._trusted_now()
            except Exception as exc: raise ProductionBlocked("TRUST.CLOCK_UNAVAILABLE") from exc
            if type(now) is not int or now < self._last_at:
                raise ProductionBlocked("TRUST.CLOCK_ROLLBACK")
            self._last_at = now
        else:
            now = None  # no lease freshness can gate a narrowing entry
        if code_digest() != self._release:
            raise ProductionBlocked("TRUST.RELEASE_CHANGED")
        try:
            self._boundary.check(required=required, release_digest=self._release,
                                 genesis_pin=self._genesis, ledger_path=self._ledger_path, now=now)
        except Exception as exc:
            raise ProductionBlocked("TRUST.REQUIRED_ROLE_UNAVAILABLE") from exc
        return now

    def admit(self, envelope):
        required = TIMED
        try:
            kind, _, _, _ = open_envelope(envelope)
        except (EnvelopeError, ValueError, TypeError):
            kind = None  # The kernel still refuses malformed statements.
        if kind in {"veto", "revoke", "freeze", "flag", "invalidate"}:
            required = BASE
        if kind in EVIDENCE or (kind is not None and kind not in SHAPES):
            required |= {"T06"}  # law-declared evidence kinds
        if kind == "reconciliation": required |= {"T08"}
        if kind in {"token", "reservation", "execution"}: required |= {"T07", "T08"}
        self._check(required)
        return self._runtime.admit(envelope, validity_check=lambda:self._check(required))

    def snapshot(self):
        self._check(BASE)
        return self._runtime.snapshot()

    def health(self, *, required_at=None):
        now = self._check(TIMED)
        return self._runtime.health(required_at=max(now, required_at or now))

    def constitutional_view(self):
        """Read-only law and obligations at one checked prefix; no authority token."""
        from maintenance.constitution import agent_view
        now = self._check(TIMED)
        snapshot = self._runtime.snapshot()
        health = self._runtime.health(required_at=now)
        return agent_view(self._runtime.kernel, snapshot, health)

    def qualify_route(self, required):
        """Check the installed T boundary for a route, without issuing a grant."""
        if not isinstance(required, (tuple, list, set, frozenset)) or not set(required) <= {f"T{i:02}" for i in range(1, 10)}:
            raise ProductionBlocked("TRUST.UNKNOWN_ROLE")
        self._check(TIMED | set(required))

    def guard(self, *, identity, signer):
        self._check(EFFECT)
        if self._effect is None:
            raise ProductionBlocked("TRUST.EFFECT_PORT_MISSING")
        return self._runtime.guard(identity=identity, signer=signer,
            effect_port=self._effect, validity_check=lambda:self._check(EFFECT))

    def deliver_due(self):
        self._check(TIMED | {"T09"})
        if not callable(getattr(self._delivery, "deliver_due", None)):
            raise ProductionBlocked("TRUST.DELIVERY_PORT_MISSING")
        return self._delivery.deliver_due(self.health())

    def close(self): return self._runtime.close()
    def __enter__(self): return self
    def __exit__(self, *_): self.close()
