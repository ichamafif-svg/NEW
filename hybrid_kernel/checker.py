"""Restrict-only checks for typed consequences, independent of K's interpreter.

This module does not import core, constitution, model, relations, obligations or
any adapter. It reads pinned declarations and exact signed bodies. Its output
can only block a decision already admitted by K. Deployment must separately
establish implementation and failure-domain independence.
"""
from __future__ import annotations

import copy
import re
from collections.abc import Mapping

from tcb.canon import digest


def relationship(pre, name, left, right):
    """Restate the closed relational vocabulary directly from the snapshot."""
    if name == "role":
        return pre["root"]["identities"].get(left, {}).get("kind") == right
    if name == "holds":
        return right not in pre["revoked"] and pre["grants"].get(right, {}).get("holder") == left
    if name == "parent":
        return left not in pre["revoked"] and pre["grants"].get(left, {}).get("parent") == right
    entity = pre.get("entities", {}).get(right if name == "owns" else left)
    if entity is None:
        return False
    return {"owns": entity.get("owner") == left,
            "type": entity.get("type") == right,
            "state": entity.get("state") == right}.get(name, False)


def eligible(pre, observation, at, raw):
    if observation["id"] in pre.get("invalidated", {}):
        return False
    spec = raw.get("instruments", {}).get(observation["property"])
    if spec is None:
        return observation["at"] <= at <= observation["at"] + raw["ttl"]["observation"]
    return (observation.get("instrument") == digest(spec)
            and observation.get("method") == spec["method"]
            and observation.get("coverage") == spec["coverage"]
            and observation["author"] in spec["sources"]
            and observation["at"] <= at <= observation["at"] + spec["fresh_ms"])


def predicates(pre, program, body, label, raw, at):
    """Bounded conjunction with no source of positive facts outside pre."""
    if not isinstance(program, dict) or set(program) != {"all"}:
        return False
    if not isinstance(program["all"], list) or not 0 < len(program["all"]) <= 16:
        return False
    for atom in program["all"]:
        if not isinstance(atom, dict) or len(atom) != 1:
            return False
        operator, args = next(iter(atom.items()))
        value = body
        if operator in ("eq", "prefix", "open"):
            for part in args[1 if operator == "open" else 0].split("."):
                value = value.get(part) if isinstance(value, Mapping) else None
        if operator == "eq":
            ok = type(value) is type(args[1]) and value == args[1]
        elif operator == "prefix":
            ok = isinstance(value, str) and value.startswith(args[1])
        elif operator == "related":
            resolve = lambda x: body.get(x[1:]) if x.startswith("$") else x
            ok = relationship(pre, args[0], resolve(args[1]), resolve(args[2]))
        elif operator == "observed":
            ok = any((o["resource"], o["property"], o["status"], o["level"]) == (body["resource"], *args)
                     and eligible(pre, o, at, raw) and not label.intersection(o["label"])
                     for o in pre["observations"].values())
        elif operator == "open":
            ok = any(o.get("type") == "law" and (o["stage"], o["key"]) == (args[0], value)
                     and not (o.get("on_due") == "lapse" and at > o["due"])
                     and o.get("label") is not None and not label.intersection(o["label"])
                     for o in pre["obligations"].values())
        elif operator == "closed_at_least":
            contracts = {d["id"]: digest(d) for d in raw["obligations"]}
            ok = len({o["key"] for o in pre["closed"].values()
                      if o["type"] == args[0] and o["at"] + raw["ttl"]["observation"] >= at
                      and o["contract"] == contracts.get(o["type"])
                      and not label.intersection(o["label"])}) >= args[1]
        else:
            return False
        if not ok:
            return False
    return True


def authority(pre, body, action, raw, fail):
    """Independent capability attenuation and freshness check for native entries."""
    chain, seen, gid = [], set(), body["under"]
    while gid != "root":
        grant = pre["grants"].get(gid)
        if grant is None or gid in seen or len(seen) >= 16:
            fail("invalid native capability chain")
        if (gid in pre["revoked"] or grant["not_after"] < body["at"]
                or grant["holder"] not in pre["root"]["identities"]):
            fail("native capability is withdrawn")
        expected = sorted(digest({"name": c, "policy": raw["conditions"].get(c)}) for c in grant["conditions"])
        if list(grant["condition_digests"]) != expected:
            fail("native capability's policy changed")
        seen.add(gid)
        chain.append(grant)
        gid = grant["parent"]
    if (not chain or chain[0]["holder"] != body["author"] or action not in chain[0]["actions"]
            or not any(p == body["resource"] or p.endswith("*") and body["resource"].startswith(p[:-1])
                       for p in chain[0]["resources"])):
        fail("native entry is outside the holder's authority")
    label = {body["author"], *(g["holder"] for g in chain)}
    for grant in chain:
        for condition in grant["conditions"]:
            if not predicates(pre, raw["conditions"][condition], body, label, raw, body["at"]):
                fail("native capability constraints do not hold")
    return chain, label


def fields(spec, values, fail):
    """Independent scalar grammar; unknown and missing fields both block."""
    if set(values) - set(spec):
        fail("undeclared native field")
    for name, kind in spec.items():
        if name not in values:
            if kind.endswith("?"):
                continue
            fail("missing native field")
        kind, value = kind.rstrip("?"), values[name]
        if kind == "str":
            ok = isinstance(value, str) and len(value) <= 4096
        elif kind == "int":
            ok = type(value) is int
        elif kind == "bool":
            ok = type(value) is bool
        else:
            expression = {"id": r"[A-Za-z0-9][A-Za-z0-9._:@/-]{0,127}",
                          "segment": r"[A-Za-z0-9][A-Za-z0-9._@-]{0,127}",
                          "digest": r"sha256:[0-9a-f]{64}"}.get(kind)
            ok = expression is not None and isinstance(value, str) and re.fullmatch(expression, value) is not None
        if not ok:
            fail("native field has an invalid scalar type")


def check(pre, record, delta, raw, fail):
    """Exact required native consequence, apart from book/law-obligation deltas."""
    kind, b = record["kind"], record["body"]
    native = [op for op in delta if op[1] in ("entities", "observations", "invalidated")]
    if kind == "invalidate":
        found = [o for o in pre["observations"].values() if o["id"] == b["evidence"]]
        role = pre["root"]["identities"][b["author"]]["kind"]
        if not found or role not in ("human", "oracle") or role == "oracle" and any(o["author"] != b["author"] for o in found):
            fail("invalid evidence restriction")
        expected = ("put", "invalidated", b["evidence"], b["id"])
    elif kind == "measurement":
        instrument = raw.get("instruments", {}).get(b["property"])
        if (instrument is None or b["author"] not in instrument["sources"]
                or b["method"] != instrument["method"] or b["coverage"] != instrument["coverage"]
                or not b["measured_at"] <= b["at"] <= b["measured_at"] + instrument["fresh_ms"]):
            fail("unqualified native measurement")
        chain, label = authority(pre, b, "observe", raw, fail)
        levels = raw["levels"]
        if "certify:" + b["level"] not in chain[0]["actions"] or levels.index(b["level"]) < levels.index(instrument["min_level"]):
            fail("measurement assurance is insufficient")
        expected = ("put", "observations", f"{b['resource']}|{b['property']}|{b['author']}",
                    {"id": b["id"], "resource": b["resource"], "property": b["property"], "status": b["status"],
                     "level": b["level"], "at": b["measured_at"], "author": b["author"], "label": sorted(label),
                     "method": b["method"], "coverage": b["coverage"], "instrument": digest(instrument), "artifact": b["artifact"]})
    else:
        if any(p == b["resource"] or p.endswith("*") and b["resource"].startswith(p[:-1]) for p in pre["frozen"]):
            fail("native resource is frozen")
        if kind == "resource":
            spec = raw.get("resources", {}).get(b["type"])
            if spec is None or b["resource"] in pre["entities"] or len(pre["entities"]) >= 4096:
                fail("invalid resource registration")
            chain, _ = authority(pre, b, "register:" + b["type"], raw, fail)
            fields(spec["fields"], b["fields"], fail)
            value = {"type": b["type"], "owner": b["author"], "state": spec["initial"], "fields": copy.deepcopy(b["fields"]),
                     "contract": digest(spec), "version": 1, "created": b["at"]}
        elif kind == "transition":
            entity = pre["entities"].get(b["resource"])
            if entity is None or digest(copy.deepcopy(entity)) != b["expected"]:
                fail("native transition has a stale prefix")
            spec = raw.get("resources", {}).get(entity["type"])
            if spec is None or digest(spec) != entity["contract"]:
                fail("native resource contract changed")
            rule = spec["transitions"].get(b["operation"])
            if rule is None or entity["state"] not in rule["from"] or set(b["changes"]) != set(rule["writes"]):
                fail("native transition is not exhaustive")
            chain, label = authority(pre, b, "transition:" + entity["type"] + ":" + b["operation"], raw, fail)
            updated = {**entity["fields"], **b["changes"]}
            fields(spec["fields"], updated, fail)
            if not predicates(pre, rule["requires"], b, label, raw, b["at"]):
                fail("native transition predicates do not hold")
            value = {**entity, "fields": updated, "state": rule["to"], "version": entity["version"] + 1}
        else:
            fail("unknown native consequence")
        spent = [op for op in delta if op[:2] == ("push", "uses")]
        if spent != [("push", "uses", g["id"], b["at"]) for g in chain]:
            fail("native mutation must charge every capability in its chain")
        for grant in chain:
            budget = grant["budget"]
            if budget and sum(1 for at in pre["uses"].get(grant["id"], ())
                              if at > b["at"] - budget["window"]) >= budget["count"]:
                fail("native mutation exceeds a capability budget")
        expected = ("put", "entities", b["resource"], value)
    if native != [expected]:
        fail("native delta must equal its exhaustive signed consequence")
