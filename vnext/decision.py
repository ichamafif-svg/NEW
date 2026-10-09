"""Deterministic constitutional transition boundary over main's real kernel.

This experimental vNext interface does not grant physical authority.
The established Journal/Guard remains the only admission and effect path.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass

from tcb.canon import canon, digest, parse
from tcb.invariants import Invariants
from tcb.kernel import Kernel, Refused, apply, empty
from tcb.release import code_digest
from .transition import normalize, transition, verify


class StaleDecision(ValueError):
    pass


@dataclass(frozen=True)
class Decision:
    """Canonical immutable result; never a dispatch token."""
    code: str
    before: str
    after: str
    law: str
    entry_bytes: bytes
    record_bytes: bytes
    delta_bytes: bytes
    state_bytes: bytes

    @property
    def record(self):
        return parse(self.record_bytes)

    @property
    def delta(self):
        return parse(self.delta_bytes)

    @property
    def state(self):
        return parse(self.state_bytes)


class DeterministicCore:
    """Evaluate a signed transition with a fresh kernel and independent checker.

    No clock lookup, I/O, credentials, journal writes or provider calls.
    The input is canonicalized and defensively copied before evaluation.
    """
    def __init__(self, *, code_pin=None):
        self.code_pin = code_pin or code_digest()

    def evaluate(self, state, entry) -> Decision:
        before_bytes = canon(copy.deepcopy(state))
        entry_bytes = canon(copy.deepcopy(entry))
        working = parse(before_bytes)
        kernel = Kernel(code_pin=self.code_pin)
        record, delta = kernel.decide(working, parse(entry_bytes))
        law = kernel.law_by_digest(record["law"])
        Invariants().check(parse(before_bytes), copy.deepcopy(record),
                           copy.deepcopy(delta), parse(entry_bytes), law)
        if canon(working) != before_bytes or canon(copy.deepcopy(state)) != before_bytes:
            raise Refused("CORE.MUTATION", "kernel changed an input state")
        if canon(copy.deepcopy(entry)) != entry_bytes:
            raise Refused("CORE.MUTATION", "kernel changed a signed entry")
        post, trace = transition(parse(before_bytes), delta)
        historical = parse(before_bytes)
        apply(historical, copy.deepcopy(delta))
        if canon(post) != canon(historical):
            raise Refused('CORE.DELTA', 'independent transition interpreter disagrees')
        return Decision(
            code=self.code_pin,
            before=digest(parse(before_bytes)),
            after=digest(post),
            law=record["law"],
            entry_bytes=entry_bytes,
            record_bytes=canon(record),
            delta_bytes=canon(normalize(delta)),
            state_bytes=canon(post),
        )

    def preview(self, state, decision: Decision):
        """Replay the decision only on its exact predecessor; no persistence."""
        if not isinstance(decision, Decision) or decision.code != self.code_pin:
            raise StaleDecision("wrong code release")
        before = parse(canon(copy.deepcopy(state)))
        if digest(before) != decision.before:
            raise StaleDecision("predecessor changed")
        after, _trace = transition(before, decision.delta)
        if digest(after) != decision.after or canon(after) != decision.state_bytes:
            raise StaleDecision("recorded delta or next state differs")
        return after

    def replay(self, signed_entries, *, initial=None):
        state = copy.deepcopy(initial) if initial is not None else empty()
        for entry in signed_entries:
            state = self.preview(state, self.evaluate(state, entry))
        return state
