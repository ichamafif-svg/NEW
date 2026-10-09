"""The accountability silo (F0-10). Deterministic, no model, outside admission.

It folds over the admitted journal, after the kernel, and never feeds back into it: a fault here can hide a gap, it can
never authorize an effect. Anyone holding the journal and the external pins recomputes the same verdict.

Guarantee: for every admitted prefix after genesis, each declared target has exactly one of a qualifying proof or one
open obligation whose `opened` and `due` never move while it stays open. An obligation past `due` escalates to the root
humans. This is visibility, not convergence: repair needs responsive actors and achievable targets; a signed source can
lie; a coverage target cannot discover assets omitted from the declared universe; nothing here delivers a notification.
"""
from __future__ import annotations

import copy

from . import policy, obligations
from .canon import digest
from .floor0 import LAPSE
from .targets import TargetError, validate

SOURCE_KINDS = ("oracle", "human", "service")


def need(target, observation, rank, at, covered: bool) -> list[str]:
    out = [] if covered else ["cover"]
    if observation is None:
        return out + ["observe"]
    stale = observation["at"] + target["fresh_ms"] < at
    low = rank[observation["level"]] < rank[target["min_level"]]
    if observation["status"] != target["expect"]:
        return out + (["observe"] if stale else []) + ["repair"]
    return out + (["observe"] if stale else []) + (["prove"] if low else [])


class Accountability:
    def __init__(self, kernel):
        """Reads the effective law in force at each entry (floors and client law) through the kernel."""
        self.kernel = kernel

    def _use(self, ks, law=None):
        law = law or self.kernel.law_of(ks)
        self.rank, self.clock_ttl, self.fresh = law.rank, law.ttl["proof"], law.ttl["observation"]
        self.targets, self.by_key = law.targets, law.by_key
        self.decls = law.obligations

    @staticmethod
    def empty() -> dict:
        return {"evidence": {}, "proofs": {}, "obligations": {}, "escalated": {}, "law": {}, "closed": {}, "measured": {},
                "carried": {}}

    # ---- fold -----------------------------------------------------------------------------------------------------
    def feed(self, a: dict, ks: dict, record: dict) -> None:
        """Called once per admitted entry, with the kernel state after that entry."""
        self._use(ks, self.kernel.law_by_digest(record["law"]))
        at, kind = record["at"], record["kind"]
        if kind == "genesis":
            a["obligations"]["clock:witness"] = {"type": "clock", "opened": at, "due": at + self.clock_ttl}
        elif kind == "checkpoint":
            a["obligations"].pop("clock:witness", None)
        elif kind == "observation":
            self._qualify(a, ks, record)
        if self.decls:
            self._law_step(a, ks, record)
        self._use(ks)
        self._sync(a, at)
        now = self._open(a, ks, at)
        for name, ob in now.items():
            if ob.get("escalates", True) and at >= ob["due"]:
                a["escalated"].setdefault(name, at)
        for name in list(a["escalated"]):
            if name not in now:
                del a["escalated"][name]           # closed: the journal prefix still shows the gap

    # ---- OBL below the refuse level: the same engine and declarations as the kernel ----------------------------
    def _law_step(self, a, ks, record):
        opens, closes, failures = obligations.step(self.decls, ("escalate", "measure"), a["law"], record,
                                                   lambda decl: self._holds(a, ks, decl, record))
        at, ident = record["at"], record["body"]["id"]
        for name, how in closes:
            ob = a["law"].pop(name)
            if how == "closed":
                a["closed"][name] = {"type": ob["stage"], "key": ob["key"], "at": at, "contract": ob["contract"]}
                self._bump(a, ob["stage"], "closed")
        for name, inst in opens:
            a["law"][name] = inst
            self._bump(a, inst["stage"], "opened")
        for decl, code, detail in failures:
            if decl["level"] == "escalate":       # a violation is an obligation already due
                a["obligations"][f"violation:{decl['id']}:{ident}"] = {
                    "type": "violation", "declaration": decl["id"], "code": code, "detail": detail,
                    "owner": record["author"], "opened": at, "due": at}
            self._bump(a, decl["id"], "violations")

    @staticmethod
    def _bump(a, decl_id, what):
        a["measured"].setdefault(decl_id, {"opened": 0, "closed": 0, "violations": 0})[what] += 1

    def _holds(self, a, ks, decl, record) -> bool:
        if decl["when"] is None:
            return True
        body = record["body"]
        law_open = [*a["law"].values(), *(ob for ob in ks["obligations"].values() if ob.get("type") == "law")]
        facts = {"request": body,
                 "observations": {(o["resource"], o["property"], o["status"], o["level"]) for o in ks["observations"].values()
                              if o["at"] + self.fresh >= record["at"]},
                 "opened": {(ob["stage"], ob["key"]) for ob in law_open if obligations.live(ob, record["at"])},
                 "closed": {(c["type"], c["key"]) for c in [*a["closed"].values(), *ks["closed"].values()]
                            if c["contract"] == self.decls.get(c["type"], {}).get("contract")}}
        try:
            return policy.evaluate(decl["when"], **facts)
        except policy.PolicyError as exc:
            raise ValueError("accountability law exceeded its work budget") from exc

    def _owner_label(self, ks, owner) -> set:
        label = {owner}
        for gid, g in ks["grants"].items():
            if g["holder"] == owner:
                while gid != "root" and gid in ks["grants"]:
                    label.add(ks["grants"][gid]["holder"])
                    gid = ks["grants"][gid]["parent"]
        return label

    def _qualify(self, a, ks, record):
        b = record["body"]
        tid = self.by_key.get((b["resource"], b["property"]))
        if tid is None:
            return
        target = self.targets[tid]
        decl = ks["root"]["identities"].get(b["author"])
        observation = ks["observations"][f"{b['resource']}|{b['property']}|{b['author']}"]
        if (b["author"] in target["sources"] and decl and decl["kind"] in SOURCE_KINDS
                and not set(observation["label"]) & self._owner_label(ks, target["owner"])):
            a["evidence"][tid] = {**observation, "target_contract": digest(target)}

    def _sync(self, a, at):
        """Open, keep or discharge exactly one obligation per target. Repetition never moves `opened` or `due`."""
        for tid in [t for t in a["evidence"] if t not in self.targets]:      # dropped by a later law
            a["evidence"].pop(tid, None)
        for tid in [t for t in a["proofs"] if t not in self.targets]:
            a["proofs"].pop(tid, None)
        for name in [n for n in a["obligations"] if n.startswith("target:") and n[7:] not in self.targets]:
            ob = a["obligations"].pop(name)            # a debt belongs to what it measures, not to its name
            a["carried"].setdefault(ob["subject"], ob["opened"])
        for tid, target in self.targets.items():
            name = "target:" + tid
            observation = a["evidence"].get(tid)
            if observation is not None and observation["target_contract"] != digest(target):
                a["evidence"].pop(tid)
                observation = None
            covered = target["kind"] == "coverage" or target["coverage"] in a["proofs"]
            needs = need(target, observation, self.rank, at, covered)
            if not needs:
                a["obligations"].pop(name, None)
                a["carried"].pop(f"{target['resource']}|{target['property']}", None)
                a["proofs"][tid] = observation["id"]
                continue
            a["proofs"].pop(tid, None)
            ob = a["obligations"].get(name)
            if ob is None:
                # A gap that began when a good proof expired opens at the expiry, not at its late detection.
                expired = (observation is not None and observation["status"] == target["expect"]
                           and observation["at"] + target["fresh_ms"] < at)
                opened = observation["at"] + target["fresh_ms"] + 1 if expired else at
                if "cover" in needs and "target:" + target["coverage"] in a["obligations"]:
                    opened = min(opened, a["obligations"]["target:" + target["coverage"]]["opened"])
                subject = f"{target['resource']}|{target['property']}"
                opened = min(opened, a["carried"].pop(subject, opened))
                ob = a["obligations"][name] = {"type": "target", "target": tid, "subject": subject, "owner": target["owner"],
                                               "opened": opened, "due": opened + target["due_ms"]}
            ob.update(owner=target["owner"], due=min(ob["due"], ob["opened"] + target["due_ms"]), needs=needs)

    def _open(self, a, ks, at) -> dict:
        out = {name: dict(ob) for name, ob in a["obligations"].items()}
        laws = [*ks["obligations"].items(), *((n, ob) for n, ob in a["law"].items() if ob["level"] == "escalate")]
        for name, ob in laws:
            if ob.get("type") == "law":
                if ob["on_due"] == "escalate":
                    out[name] = dict(ob)
                elif at <= ob["due"]:
                    out[name] = {**ob, "escalates": False}
                continue
        for name, ob in ks["obligations"].items():
            if ob.get("type") == "law":
                continue
            if ob["stage"] in LAPSE:
                if at <= ob["due"]:
                    out[name] = {"type": "protocol", **ob, "escalates": False}   # it lapses instead of escalating
            else:
                out[name] = {"type": "protocol", **ob}
        return out

    # ---- verdict --------------------------------------------------------------------------------------------------
    def health(self, a: dict, ks: dict, *, required_at: int | None = None) -> dict:
        """As of signed ledger time. A caller's trusted `required_at` beyond it is a visible clock gap, and every
        obligation already due by then escalates: a silent witness cannot hold a verdict in IN_PROGRESS."""
        if not ks["size"]:
            raise ValueError("an initialized authenticated ledger is required")
        self._use(ks)
        if required_at is not None and (type(required_at) is not int or required_at < 0):
            raise ValueError("required_at is a nonnegative trusted millisecond timestamp")
        at = ks["last_at"]
        horizon = max(at, required_at or 0)
        # External trusted time can expose stale evidence without manufacturing
        # an admitted entry or changing the signed ledger's time.
        a = copy.deepcopy(a)
        self._sync(a, horizon)
        humans = sorted(i for i, d in ks["root"]["identities"].items() if d["kind"] == "human")
        open_, escalated = [], []
        for name, ob in sorted(self._open(a, ks, horizon).items()):
            item = {"obligation": name, **ob}
            if name in a["escalated"]:
                item["escalated_at"] = a["escalated"][name]
            if item.pop("escalates", True) and horizon >= ob["due"]:
                item["escalated_to"] = humans
                escalated.append(item)
            else:
                open_.append(item)
        if required_at is not None and required_at > at:
            gap = {"obligation": "clock:after-ledger", "type": "clock_gap", "owner": humans[0],
                   "opened": at + 1, "due": at + self.clock_ttl,
                   "requested_at": required_at, "ledger_at": at}
            if horizon >= gap["due"]:
                gap["escalated_to"] = humans
                escalated.append(gap)
            else:
                open_.append(gap)
        proven = [{"target": t, "evidence": a["proofs"][t]} for t in self.targets if t in a["proofs"]]
        state = "ESCALATED" if escalated else ("PROVEN" if not open_ and len(proven) == len(self.targets) else "IN_PROGRESS")
        measured = {d: {**a["measured"].get(d, {"opened": 0, "closed": 0, "violations": 0}),
                        "open": sum(1 for ob in a["law"].values() if ob["stage"] == d and obligations.live(ob, horizon))}
                    for d, decl in self.decls.items() if decl["level"] == "measure"}
        return {"as_of": at, "evaluated_at": horizon,
                "witness_at": ks["anchor_at"] if ks["witnessed"] else None, "state": state,
                "proven": proven, "open": open_, "escalated": escalated, "measured": measured}
