"""Canonical, bounded model for constitutional judgment.

Relations are projections of authenticated state, never an adapter supplied
permission graph. A Decision contains the exhaustive consequence, not an
executable capability. Only the anchored admission boundary commits it.
"""
from __future__ import annotations

import copy
from collections.abc import Mapping
from dataclasses import dataclass

from tcb.canon import canon, digest, parse
from tcb.shapes import ID, RESOURCE

VERSION = "standard-hybrid/1"
MAX_ENTRY_BYTES = 1 << 20
MAX_ENTITIES = 4096
MAX_FIELDS = 32
MAX_STATES = 32
MAX_TRANSITIONS = 64
RELATIONS = frozenset({"role", "holds", "parent", "owns", "type", "state"})


@dataclass(frozen=True, order=True)
class Relation:
    name: str
    left: str
    right: str

    def wire(self):
        return [self.name, self.left, self.right]


@dataclass(frozen=True)
class Decision:
    """Serialized snapshots prevent post-judgment mutation through nested dicts."""
    verdict: str
    code: str
    before: str
    after: str | None
    entry_bytes: bytes
    record_bytes: bytes | None
    delta_bytes: bytes
    detail: str = ""

    @property
    def record(self):
        return parse(self.record_bytes) if self.record_bytes is not None else None

    @property
    def delta(self):
        return parse(self.delta_bytes, max_bytes=64 << 20)

    def wire(self):
        return {"version": VERSION, "verdict": self.verdict, "code": self.code,
                "before": self.before, "after": self.after,
                "entry": parse(self.entry_bytes), "record": self.record,
                "delta": self.delta, "detail": self.detail}


def detached(value):
    """Detach read-only views without weakening the canonical scalar grammar."""
    if isinstance(value, Mapping):
        return {k: detached(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [detached(v) for v in value]
    return value


def relations(state):
    """Finite typed facts. Revoked grants remain historical, not permitting facts.

    Capability relations do not certify usable authority: every privileged
    transition still rechecks the entire chain and its temporal constraints.
    """
    rows = set()
    if state["root"] is not None:
        for ident, decl in state["root"]["identities"].items():
            rows.add(Relation("role", ident, decl["kind"]))
    for gid, grant in state["grants"].items():
        if gid not in state["revoked"]:
            rows.add(Relation("holds", grant["holder"], gid))
            rows.add(Relation("parent", gid, grant["parent"]))
    for resource, entity in state.get("entities", {}).items():
        rows.add(Relation("owns", entity["owner"], resource))
        rows.add(Relation("type", resource, entity["type"]))
        rows.add(Relation("state", resource, entity["state"]))
    return tuple(sorted(rows))


def relation_facts(state, request, atoms):
    """Exact bound queries; irrelevant relations cannot exhaust a proof budget."""
    rows = set()
    for operator, args in atoms:
        if operator != "related":
            continue
        name, left, right = args
        resolve = lambda x: request.get(x[1:]) if x.startswith("$") else x
        left, right = resolve(left), resolve(right)
        if not isinstance(left, str) or not isinstance(right, str):
            continue
        if name == "role":
            holds = state["root"]["identities"].get(left, {}).get("kind") == right
        elif name == "holds":
            holds = right not in state["revoked"] and state["grants"].get(right, {}).get("holder") == left
        elif name == "parent":
            holds = left not in state["revoked"] and state["grants"].get(left, {}).get("parent") == right
        else:
            entity = state["entities"].get(right if name == "owns" else left)
            holds = entity is not None and {"owns": entity.get("owner") == left,
                    "type": entity.get("type") == right, "state": entity.get("state") == right}.get(name, False)
        if holds:
            rows.add((name, left, right))
    return rows


def check_resource_types(raw, program):
    """Versioned schemas and finite transitions; no Python or opaque callbacks.

    Writes can touch declared scalar fields only. Ownership, identity, type,
    authority, law, evidence and debt are closed constitutional primitives.
    """
    from tcb.shapes import SCALARS, check_spec, ShapeError
    if not isinstance(raw, dict) or len(raw) > 64:
        raise ValueError("resources is a map of at most 64 types")
    result = {}
    for name, spec in raw.items():
        if (not isinstance(name, str) or not ID.fullmatch(name)
                or not isinstance(spec, dict)
                or set(spec) != {"fields", "states", "initial", "transitions"}):
            raise ValueError("resource type is fields, states, initial, transitions")
        fields, states, transitions = spec["fields"], spec["states"], spec["transitions"]
        if not isinstance(fields, dict) or len(fields) > MAX_FIELDS:
            raise ValueError("resource fields exceed bound")
        try:
            check_spec(fields, SCALARS)
        except ShapeError as exc:
            raise ValueError(str(exc)) from None
        if (not isinstance(states, list) or not 0 < len(states) <= MAX_STATES
                or not all(isinstance(s, str) and ID.fullmatch(s) for s in states)
                or len(set(states)) != len(states) or spec["initial"] not in states):
            raise ValueError("resource states are distinct names with an initial state")
        if not isinstance(transitions, dict) or len(transitions) > MAX_TRANSITIONS:
            raise ValueError("resource transition count exceeds bound")
        compiled = {}
        for operation, rule in transitions.items():
            if (not isinstance(operation, str) or not ID.fullmatch(operation)
                    or not isinstance(rule, dict)
                    or set(rule) != {"from", "to", "requires", "writes"}):
                raise ValueError("transition is from, to, requires, writes")
            if (not isinstance(rule["from"], list) or not rule["from"]
                    or not all(isinstance(s, str) and s in states for s in rule["from"])
                    or len(set(rule["from"])) != len(rule["from"])
                    or rule["to"] not in states):
                raise ValueError("transition endpoints belong to its resource type")
            writes = rule["writes"]
            if (not isinstance(writes, list) or not all(isinstance(f, str) and f in fields for f in writes)
                    or len(set(writes)) != len(writes)):
                raise ValueError("writes names distinct declared fields")
            compiled[operation] = {**copy.deepcopy(rule), "requires": program(rule["requires"])}
        result[name] = {**copy.deepcopy(spec), "transitions": compiled, "contract": digest(spec)}
    return result


def check_instruments(raw, rank):
    """Evidence eligibility is pinned law, separate from signature validity.

    Coverage and method are explicit attestations of a qualified T06 source.
    K can check their binding; physical measurement truth remains a T contract.
    """
    if not isinstance(raw, dict) or len(raw) > 128:
        raise ValueError("instruments is a bounded map")
    out = {}
    for prop, spec in raw.items():
        if (not isinstance(prop, str) or not ID.fullmatch(prop)
                or not isinstance(spec, dict)
                or set(spec) != {"method", "coverage", "sources", "min_level", "fresh_ms"}):
            raise ValueError("instrument is method, coverage, sources, min_level, fresh_ms")
        if not isinstance(spec["method"], str) or not ID.fullmatch(spec["method"]):
            raise ValueError("instrument method is a stable name")
        if not isinstance(spec["coverage"], str) or not RESOURCE.fullmatch(spec["coverage"]):
            raise ValueError("instrument coverage is an exact resource")
        sources = spec["sources"]
        if (not isinstance(sources, list) or not 0 < len(sources) <= 32
                or not all(isinstance(s, str) and ID.fullmatch(s) for s in sources)
                or len(set(sources)) != len(sources)):
            raise ValueError("instrument sources are distinct principal names")
        if (spec["min_level"] not in rank or type(spec["fresh_ms"]) is not int
                or not 0 < spec["fresh_ms"] <= 365 * 86400000):
            raise ValueError("instrument level and freshness must be bounded")
        out[prop] = {**copy.deepcopy(spec), "contract": digest(spec)}
    return out
