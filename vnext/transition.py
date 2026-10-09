"""Pure, closed transition algebra: one syntax for every constitutional state change.

This module intentionally knows nothing about grants, evidence, Git or providers.
It specifies what an admitted decision means *as a mutation* and makes the
entire before/after relation checkable. Semantic admission remains the job of
the constitutional judge. The effectful persistence boundary is separate.
"""
from __future__ import annotations

import copy

from tcb.canon import canon, digest, parse


class TransitionError(ValueError):
    pass


def canonical(value):
    """Validate and return a detached, canonical JSON value."""
    return parse(canon(value))


def normalize(delta):
    """Closed, bounded instruction grammar. No polymorphic or implicit writes."""
    if not isinstance(delta, (list, tuple)) or len(delta) > 4096:
        raise TransitionError("delta is a bounded sequence")
    ops = []
    for raw in delta:
        if not isinstance(raw, (list, tuple)) or not raw:
            raise TransitionError("malformed instruction")
        op = raw[0]
        if op not in ("set", "put", "drop", "push"):
            raise TransitionError("unknown instruction")
        length = {"set": 3, "put": 4, "drop": 3, "push": 4}[op]
        if len(raw) != length or not isinstance(raw[1], str):
            raise TransitionError("invalid instruction shape")
        if op != "set" and not isinstance(raw[2], str):
            raise TransitionError("map key is not a string")
        ops.append(canonical(list(raw)))
    return ops


def transition(state, delta):
    """Execute exactly the delta on a detached canonical state, failing closed.

    Intermediate writes are validated and cannot silently create new state
    sections. The returned trace binds every individual mutation, making the
    transition relation independently inspectable.
    """
    before = canonical(state)
    if not isinstance(before, dict):
        raise TransitionError("state must be an object")
    current = copy.deepcopy(before)
    trace = []
    for instruction in normalize(delta):
        op, name = instruction[:2]
        if name not in current:
            raise TransitionError("unknown state section")
        if op == "set":
            current[name] = instruction[2]
        else:
            target = current[name]
            if not isinstance(target, dict):
                raise TransitionError("expected a state map")
            key = instruction[2]
            if op == "put":
                target[key] = instruction[3]
            elif op == "drop":
                if key not in target:
                    raise TransitionError("cannot drop absent key")
                del target[key]
            else:
                prior = target.get(key, [])
                if not isinstance(prior, list):
                    raise TransitionError("cannot push into non-list")
                target[key] = [*prior, instruction[3]]
        trace.append({"instruction": instruction, "post": digest(current)})
    return current, trace


def verify(state, delta, expected):
    """One check for every state field: no undeclared mutations permitted."""
    actual, trace = transition(state, delta)
    if canon(actual) != canon(expected):
        raise TransitionError("decision's post-state differs from exhaustive delta application")
    return trace
