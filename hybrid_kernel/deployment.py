"""Route-specific K/T integration; operator-controlled physical ports."""
from __future__ import annotations

from tcb.crypto import EnvelopeError, open_envelope
from tcb.effects import EffectPort, NotDispatched
from tcb.release import code_digest
from .core import SHAPES
from .runtime import ConstitutionalRuntime


class ProductionBlocked(RuntimeError):
    pass


class LawBoundPort(EffectPort):
    """Recheck operation-specific T before the first provider byte leaves."""

    def __init__(self, port, deployment):
        self.port, self.deployment = port, deployment

    def perform(self, judged, expected_bytes, reservation_key):
        try:
            state = self.deployment._runtime.snapshot()
            op = self.deployment._runtime.kernel.law_of(state).ops[judged["op"]]
            self.deployment.qualify_route(op["trusted"])
        except Exception as exc:
            raise NotDispatched("operation trust unavailable before dispatch") from exc
        return self.port.perform(judged, expected_bytes, reservation_key)


BASE = frozenset({"T01", "T02", "T04", "T05"})
TIMED = BASE | {"T03"}
EFFECT = TIMED | {"T07", "T08"}
EVIDENCE = {"measurement", "observation", "evidence"}


class GovernedDeployment:
    """Contract boundary. The installation must provision trusted implementations."""

    def __init__(self, *, ledger_path, pin_store, genesis_pin, trust_boundary,
                 trusted_now, effect_port=None, delivery_port=None, reconciliation_port=None):
        if not callable(trusted_now) or not callable(getattr(trust_boundary, "check", None)):
            raise ProductionBlocked("TRUST.BOUNDARY_REQUIRED")
        self._boundary, self._trusted_now = trust_boundary, trusted_now
        self._effect, self._delivery, self._reconciliation = effect_port, delivery_port, reconciliation_port
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
            kind, body, _, _ = open_envelope(envelope)
        except (EnvelopeError, ValueError, TypeError):
            kind = None  # The kernel still refuses malformed statements.
            body = {}
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

    def status(self):
        """Fault-safe operator visibility, even when timed routes are unavailable."""
        try:
            self._check(BASE)
            state = self._runtime.snapshot()
            basis = {"head": state["head"], "size": state["size"], "genesis": state["domain"]}
            try:
                health = self.health()
                return {"state": health.get("state", "FAULT"), "basis": basis,
                        "open": len(health.get("open", [])), "escalated": len(health.get("escalated", []))}
            except Exception:
                return {"state": "FAULT", "basis": basis, "reason": "TIMED_AUDIT_UNAVAILABLE"}
        except Exception:
            return {"state": "FAULT", "basis": None, "reason": "TRUSTED_PREFIX_UNAVAILABLE"}

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
        if "T07" in required and not isinstance(self._effect, EffectPort): raise ProductionBlocked("TRUST.EFFECT_PORT_MISSING")
        if "T08" in required and not callable(getattr(self._reconciliation, "readback", None)): raise ProductionBlocked("TRUST.RECONCILIATION_PORT_MISSING")
        if "T09" in required and not callable(getattr(self._delivery, "deliver_due", None)): raise ProductionBlocked("TRUST.DELIVERY_PORT_MISSING")

    def guard(self, *, identity, signer):
        self._check(EFFECT)
        if not isinstance(self._effect, EffectPort):
            raise ProductionBlocked("TRUST.EFFECT_PORT_MISSING")
        return self._runtime.guard(identity=identity, signer=signer,
            effect_port=LawBoundPort(self._effect, self), validity_check=lambda:self._check(EFFECT))

    def deliver_due(self):
        self._check(TIMED | {"T09"})
        if not callable(getattr(self._delivery, "deliver_due", None)):
            raise ProductionBlocked("TRUST.DELIVERY_PORT_MISSING")
        return self._delivery.deliver_due(self.health())

    def dispatch_due(self, *, identity, signer):
        """Trusted-side progress of already admitted effects, never an agent API."""
        from tcb.floor0 import line_state
        now = self._check(EFFECT)
        guard = self.guard(identity=identity, signer=signer)
        results = {}
        state = self.snapshot()
        for intent_id in sorted(state["intents"]):
            phase = line_state(state["line"], intent_id, now)
            if phase not in ("intended", "tokened"):
                continue
            try:
                at = max(self._check(EFFECT), self.snapshot()["last_at"] + 1)
                if phase == "intended":
                    guard.issue(intent_id, at)
                token = self.snapshot()["token_of"][intent_id]
                results[intent_id] = guard.redeem(token, max(self._check(EFFECT), self.snapshot()["last_at"] + 1))
            except Exception as exc:
                results[intent_id] = {"blocked": type(exc).__name__}
        return results

    def reconcile_due(self):
        """Ask an installed independent T08 instrument for signed readback."""
        from tcb.floor0 import line_state
        now = self._check(TIMED | {"T08"})
        if not callable(getattr(self._reconciliation, "readback", None)):
            raise ProductionBlocked("TRUST.RECONCILIATION_PORT_MISSING")
        state = self.snapshot()
        results = {}
        for intent_id in sorted(state["intents"]):
            if line_state(state["line"], intent_id, now) not in ("uncertain", "expired"):
                continue
            try:
                envelope = self._reconciliation.readback(intent_id, state)
                results[intent_id] = self.admit(envelope) if envelope is not None else "UNKNOWN"
            except Exception as exc:
                results[intent_id] = {"blocked": type(exc).__name__}
        return results

    def close(self): return self._runtime.close()
    def __enter__(self): return self
    def __exit__(self, *_): self.close()
