"""OBL: one engine of linear obligations for every level, inside and outside the TCB.

The law declares obligation types. Each names the entries that open it, close it, or need it open (gates), a key
taken from the entry, a deadline, and a level:

    refuse    applied by the kernel: a gate or close that fails refuses the entry
    escalate  applied by accountability: a failure opens a violation that escalates at once
    measure   applied by accountability: a failure is counted and published, never escalated

The same declaration can move between levels without being rewritten. An instance is named "<type>:<key>". Opening
an open key keeps it (one instance per key), replaces it, or refuses, as declared. Nothing changes because time
passes: a deadline lapses an instance (it stops gating and can be reopened) or escalates it, as declared.

This module is pure: it reads the open instances and one admitted record, and returns what to open and close."""
from __future__ import annotations

import re
from collections.abc import Mapping
from tcb.canon import digest

LEVELS = ("refuse", "escalate", "measure")
CONSTRAINABLE = ("act", "attest", "attenuate")   # a refuse-level rule never touches widen, restrict or witness kinds
RESERVED = {"pending", "unredeemed", "reconcile", "proof", "target", "clock", "violation"}
PATH = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,63}(\.[A-Za-z][A-Za-z0-9_]{0,63})?$")
NAME = re.compile(r"^[a-z][a-z0-9-]{0,63}$")


class DeclarationError(ValueError):
    pass


def _rule(raw, where: str, kinds) -> dict:
    if not isinstance(raw, dict) or not {"kind", "key"} <= set(raw) or set(raw) - {"kind", "key", "where", "op"}:
        raise DeclarationError(f"{where}: a rule is {{kind, key, where?, op?}}")
    if raw["kind"] not in kinds or not isinstance(raw["key"], str) or not PATH.fullmatch(raw["key"]):
        raise DeclarationError(f"{where}: unknown kind or bad key path")
    cond = raw.get("where", {})
    if not isinstance(cond, dict) or len(cond) > 8 or not all(
            isinstance(k, str) and PATH.fullmatch(k) and type(v) in (str, int) for k, v in cond.items()):
        raise DeclarationError(f"{where}: where maps field paths to strings or integers")
    if "op" in raw and (raw["kind"] != "intent" or not isinstance(raw["op"], str)):
        raise DeclarationError(f"{where}: op filters intents only")
    return {"kind": raw["kind"], "key": raw["key"], "where": dict(cond), "op": raw.get("op")}


def validate(raw, kinds, program) -> dict:
    """kinds: every entry kind of this law and its polarity. program(rules) validates a finite positive `when`.
    Polarity is typed here (F0-5): a refuse-level rule may only constrain kinds that act, attest or attenuate, so no
    law can block a restriction, a witness or the widening protocol that would repair it."""
    if raw is None:
        return {}
    if not isinstance(raw, list) or len(raw) > 64:
        raise DeclarationError("obligations is a list of at most 64 declarations")
    decls = {}
    allowed = {"id", "level", "due_ms", "on_due", "open", "close", "gate", "reopen", "when"}
    for d in raw:
        if not isinstance(d, dict) or not {"id", "level", "due_ms", "on_due", "open"} <= set(d) or set(d) - allowed:
            raise DeclarationError("a declaration is {id, level, due_ms, on_due, open, close?, gate?, reopen?, when?}")
        ident = d["id"]
        if not isinstance(ident, str) or not NAME.fullmatch(ident) or ident in RESERVED or ident in decls:
            raise DeclarationError(f"{ident}: a new lowercase name")
        if d["level"] not in LEVELS or d["on_due"] not in ("lapse", "escalate"):
            raise DeclarationError(f"{ident}: level in {LEVELS}, on_due lapse or escalate")
        if type(d["due_ms"]) is not int or not 0 < d["due_ms"] <= 365 * 86_400_000:
            raise DeclarationError(f"{ident}: due_ms is a positive bounded duration")
        if d.get("reopen", "keep") not in ("keep", "replace", "refuse"):
            raise DeclarationError(f"{ident}: reopen is keep, replace or refuse")
        rules = {}
        for part in ("open", "close", "gate"):
            items = d.get(part, [])
            if not isinstance(items, list) or len(items) > 16 or (part == "open" and not items):
                raise DeclarationError(f"{ident}: {part} is a list (open is not empty)")
            rules[part] = [_rule(r, f"{ident}.{part}", kinds) for r in items]
            if d["level"] == "refuse" and any(kinds[r["kind"]] not in CONSTRAINABLE for r in rules[part]):
                raise DeclarationError(f"{ident}.{part}: a refuse-level rule constrains only {CONSTRAINABLE} kinds")
        decls[ident] = {"contract": digest(d), "id": ident, "level": d["level"], "due_ms": d["due_ms"], "on_due": d["on_due"],
                        "reopen": d.get("reopen", "keep"), **rules,
                        "when": program(d["when"]) if "when" in d else None}
    return decls


def get(body: dict, path: str):
    value = body
    for part in path.split("."):
        value = value.get(part) if isinstance(value, Mapping) else None
    return value if isinstance(value, (str, int)) and not isinstance(value, bool) else None


def key_of(rule: dict, record: dict):
    """The instance key this record designates under this rule, or None if the rule does not apply."""
    body = record["body"]
    if record["kind"] != rule["kind"] or (rule["op"] is not None and body.get("op") != rule["op"]):
        return None
    if any(get(body, k) != v for k, v in rule["where"].items()):
        return None
    return get(body, rule["key"])


def live(instance: dict, at: int) -> bool:
    return not (instance.get("on_due") == "lapse" and at > instance["due"])


def step(decls, levels, open_: dict, record: dict, holds, admits=lambda instance: True) -> tuple[list, list, list]:
    """Returns (opens [(name, instance)], closes [(name, how)], failures [(decl, code, detail)]) for one record.
    `how` is "closed" when a closing entry satisfied the instance, "replaced" when a new opening supersedes it.

    `holds(decl)` evaluates the declaration's `when` condition for this record (True when there is none).
    `admits(instance)` says whether an open instance may satisfy a gate for this record (the kernel: only an instance
    opened by a chain independent of the record's, F0-8)."""
    at, opens, closes, failures = record["at"], [], {}, []
    for d in (d for d in decls.values() if d["level"] in levels):
        for rule in d["gate"]:
            key = key_of(rule, record)
            if key is not None:
                inst = open_.get(f"{d['id']}:{key}")
                if inst is None or not live(inst, at) or inst["contract"] != d["contract"] or not admits(inst):
                    failures.append((d, "OBL.GATE", f"{record['kind']} needs {d['id']}:{key} open"))
        for rule in d["close"]:
            key = key_of(rule, record)
            if key is not None:
                name = f"{d['id']}:{key}"
                if name in open_ and open_[name]["contract"] != d["contract"]:
                    failures.append((d, "OBL.CONTRACT", f"{name} belongs to another declaration"))
                elif name in open_ and live(open_[name], at) and name not in closes:
                    closes[name] = "closed"
                else:
                    failures.append((d, "OBL.NOT_OPEN", f"{name} is not open"))
        for rule in d["open"]:
            key = key_of(rule, record)
            if key is None or not holds(d):
                continue
            name = f"{d['id']}:{key}"
            current = open_.get(name)
            if current is not None and live(current, at) and name not in closes:
                if d["reopen"] == "keep":
                    continue
                if d["reopen"] == "refuse":
                    failures.append((d, "OBL.ALREADY_OPEN", f"{name} is already open"))
                    continue
                closes[name] = "replaced"
            elif current is not None and name not in closes:
                closes[name] = "replaced"                # a lapsed instance is replaced by the new one
            opens.append((name, {"stage": d["id"], "type": "law", "level": d["level"], "key": key, "opened": at,
                                 "due": at + d["due_ms"], "on_due": d["on_due"], "owner": record["author"], "contract": d["contract"]}))
    return opens, list(closes.items()), failures
