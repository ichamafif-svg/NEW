"""The admission kernel. Pure and total: `decide(state, entry)` reads the state, never mutates it, and returns either a
Refused or (record, delta). `apply(state, delta)` is the only mutation, and a delta is data: put / drop / set / push.
Every transition is therefore caused by exactly one signed entry (F0-4); nothing changes because time passed.

Admission of an entry, in this order:
  HIST     it extends the head; its time runs forward and stays within reach of the last witnessed time
  SIG      every signature verifies against the root in force; the subject names this ledger's genesis
  TYPE     the body is exactly of its declared shape (effect arguments included)
  POLARITY one gate per polarity (F0-5):
             widen      a human of the root states it, k humans sign; it only becomes a proposal
             restrict   any eligible single party, immediately
             witness    a quorum of witnesses; the only way the attested anchor advances
             attenuate, act, attest   under a capability chain (CAP below)
  CAP      the author holds a chain from the root that covers the action, every condition derives `ok` from the
           statement and from fresh observations attested by chains independent of the author's
  OBL      linear obligations: an effect line consumes what it needs and opens what follows
  NIV/PROV a level is claimed only by a chain that may certify it; a proof comes from an independent chain
Refusal names the gate and the reason; nothing is ever admitted by default."""
from __future__ import annotations

import copy
import threading

from . import policy, obligations
from .canon import CanonError, digest
from .crypto import ALGORITHMS, EnvelopeError, canonical_public, keyid, open_envelope, subject_name, verify
from .floor0 import KINDS, LAPSE, LINE, MAX_AHEAD_MS, MIN_HUMANS, POLARITY, RESTRICT_BY, line_state
from .law import Law, LawError, compose
from .release import code_digest
from .shapes import ID, PATTERN, RESOURCE, ShapeError, build, covers, within

PROPOSAL = {"override": "bool?"}
SCOPE = {"holder": "id", "actions": "list", "resources": "list", "conditions": "list", "budget": "map?", "not_after": "int"}
SHAPES = {
    "genesis": {"root": "map", "law": "map", "code": "digest"},
    "law": {"release": "map", **PROPOSAL},
    "rotate": {"root": "map", **PROPOSAL},
    "grant": {**SCOPE, **PROPOSAL},
    "unfreeze": {"scope": "pattern", **PROPOSAL},
    "activate": {"proposal": "id"},
    "veto": {"proposal": "id"},
    "delegate": {"parent": "id", **SCOPE},
    "revoke": {"grant": "id"},
    "freeze": {"scope": "pattern"},
    "flag": {"intent": "id"},
    "heartbeat": {"seen": "int"},
    "checkpoint": {"size": "int", "head": "digest"},
    "intent": {"under": "id", "op": "id", "args": "map", "retry_of": "id?"},
    "token": {"intent": "id", "args_digest": "digest"},
    "reservation": {"token": "id"},
    "execution": {"token": "id", "result": "str"},
    "reconciliation": {"under": "id", "intent": "id", "result": "str"},
    "observation": {"under": "id", "resource": "resource", "property": "str", "status": "str", "level": "str"},
}
assert set(SHAPES) == set(POLARITY), "every kernel kind has exactly one polarity"

MAX_CHAIN = 16


class Refused(Exception):
    def __init__(self, code: str, detail: str = ""):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail = code, detail


def no(code: str, detail: str = ""):
    raise Refused(code, detail)


# ---- the root ------------------------------------------------------------------------------------------------------
def check_root(root) -> None:
    if not isinstance(root, dict) or set(root) != {"threshold", "identities"}:
        no("TYPE.ROOT", "a root is {threshold, identities}")
    ids = root["identities"]
    if not isinstance(ids, dict) or not 0 < len(ids) <= 256:
        no("TYPE.ROOT", "a root lists identities")
    seen = set()
    for ident, decl in ids.items():
        if not ID.fullmatch(ident) or not isinstance(decl, dict) or set(decl) != {"kind", "keys"} or decl["kind"] not in KINDS:
            no("TYPE.ROOT", f"{ident}: {{kind, keys}} with a known kind")
        if not isinstance(decl["keys"], list) or not 0 < len(decl["keys"]) <= 8:
            no("TYPE.ROOT", f"{ident}: one to eight keys")
        for key in decl["keys"]:
            if not isinstance(key, dict) or key.get("alg") not in ALGORITHMS or not isinstance(key.get("public"), str):
                no("TYPE.ROOT", f"{ident}: bad key")
            extra = {"rp_id", "origins"} if key["alg"] == "webauthn-es256" else set()
            if set(key) != {"alg", "public", "keyid"} | extra:
                no("TYPE.ROOT", f"{ident}: key fields")
            if extra and (not isinstance(key["rp_id"], str) or not isinstance(key["origins"], list) or not key["origins"]
                          or not all(isinstance(o, str) for o in key["origins"])):
                no("TYPE.ROOT", f"{ident}: a passkey names its relying party and origins")
            try:
                kid = keyid(key["public"])
                if not canonical_public(key["alg"], key["public"]):
                    raise EnvelopeError("not canonical")
            except EnvelopeError:
                no("TYPE.ROOT", f"{ident}: a public key in its one canonical encoding")
            if key["keyid"] != kid or kid in seen:
                no("TYPE.ROOT", f"{ident}: bad or repeated key")
            seen.add(kid)
    n, k = len(humans(root)), root["threshold"]
    if type(k) is not int or k < MIN_HUMANS or n < k + 2:
        no("FLOOR0.ROOT", f"a quorum of at least {MIN_HUMANS} humans and two additional humans for veto recovery")


def humans(root) -> set:
    return {i for i, d in root["identities"].items() if d["kind"] == "human"}


def kind_of(root, ident) -> str | None:
    decl = root["identities"].get(ident) if isinstance(ident, str) else None
    return decl["kind"] if decl else None


def empty() -> dict:
    return {"size": 0, "head": None, "domain": None, "last_at": 0, "anchor_at": 0, "witnessed": False,
            "root": None, "root_digest": None, "code": None, "law": None,
            "statements": {}, "proposals": {}, "grants": {}, "revoked": {}, "frozen": {}, "flags": {}, "heartbeats": {},
            "obligations": {}, "closed": {}, "intents": {}, "tokens": {}, "token_of": {}, "reserved": {}, "executed": {}, "uses": {}, "line": {},
            "observations": {}}


def apply(state: dict, delta: list) -> dict:
    """The only mutation of kernel state. Records put here are never mutated afterwards."""
    for op in delta:
        if op[0] == "put":
            state[op[1]][op[2]] = op[3]
        elif op[0] == "drop":
            del state[op[1]][op[2]]
        elif op[0] == "set":
            state[op[1]] = op[2]
        elif op[0] == "push":
            state[op[1]][op[2]] = (*state[op[1]].get(op[2], ()), op[3])
        else:
            raise ValueError(f"unknown delta {op[0]}")
    return state


def lapsed(ob: dict, at: int) -> bool:
    """Before any effect, time lapses an obligation; after a reservation, nothing lapses (F0-6)."""
    return (ob["stage"] in LAPSE or ob.get("on_due") == "lapse") and at > ob["due"]


class Kernel:
    """The kernel carries no client law: the genesis brings the first one, `law` entries replace it by widening, and
    every entry is judged under the floors of this release composed with the client law in force at its position."""

    def __init__(self, *, code_pin=None):
        self.code_pin = code_pin or code_digest()
        self._laws: dict[str, Law] = {}
        self._local = threading.local()

    @property
    def law(self) -> Law:
        """The effective law of the entry being judged (per thread)."""
        return self._local.law

    def load(self, client) -> Law:
        """The floors composed with this client law, validated, cached by effective digest."""
        try:
            release = compose(copy.deepcopy(client))
            ident = digest(release)
            if ident not in self._laws:
                self._laws[ident] = Law(release, ident)
            return self._laws[ident]
        except (ValueError, TypeError, KeyError) as exc:
            raise LawError(str(exc)) from None

    def law_of(self, state) -> Law:
        return self._laws.get(state["law"]["digest"]) or self.load(state["law"]["client"])

    def law_by_digest(self, ident: str) -> Law:
        return self._laws[ident]

    # ---- the whole ledger ---------------------------------------------------------------------------------------
    def replay(self, entries: list) -> dict:
        state = empty()
        for e in entries:
            self.advance(state, e)
        return state

    def advance(self, state: dict, entry: dict) -> dict:
        record, delta = self.decide(state, entry)
        apply(state, delta)
        return record

    def admit(self, state: dict, entry: dict) -> tuple[bool, str, str]:
        try:
            self.decide(state, entry)
            return True, "ADMITTED", ""
        except Refused as r:
            return False, r.code, r.detail

    def decide(self, state: dict, entry: dict) -> tuple[dict, list]:
        """Total: any input yields a verdict. An unexpected input error is a refusal, never an admission."""
        try:
            return self._decide(state, entry)
        except Refused:
            raise
        except (KeyError, TypeError, ValueError, AttributeError, IndexError, RecursionError, CanonError) as exc:
            raise Refused("KERNEL.MALFORMED", type(exc).__name__) from None

    # ---- one entry ----------------------------------------------------------------------------------------------
    def _decide(self, s: dict, entry: dict) -> tuple[dict, list]:
        if not isinstance(entry, dict) or set(entry) != {"seq", "prev", "envelope"}:
            no("HIST.SHAPE", "an entry is {seq, prev, envelope}")
        if type(entry["seq"]) is not int or entry["seq"] != s["size"] or entry["prev"] != s["head"]:
            no("HIST.CHAIN", "the entry does not extend the head")
        try:
            kind, body, message, name = open_envelope(entry["envelope"])
        except EnvelopeError as exc:
            no("SIG.ENVELOPE", str(exc))
        law = self.law_of(s) if s["size"] else None
        shape = SHAPES.get(kind) or (law.evidence.get(kind) if law else None)
        if shape is None:
            no("TYPE.KIND", f"{kind} is not a kind of this law")
        try:
            build(shape, body)
        except ShapeError as exc:
            no("TYPE.SHAPE", str(exc))
        genesis = kind == "genesis"
        if genesis != (s["size"] == 0):
            no("HIST.GENESIS", "the genesis is the first entry and only the first")
        if genesis:
            check_root(body["root"])
            try:
                law = self.load(body["law"])
            except LawError as exc:
                no("LAW.INVALID", str(exc))
        self._local.law = law
        root = body["root"] if genesis else s["root"]
        if name != subject_name("genesis" if genesis else s["domain"], kind, body["id"]):
            no("SIG.DOMAIN", "the statement names another ledger")
        signers = self._signers(root, entry["envelope"], message)
        if body["author"] not in signers:
            no("SIG.AUTHOR", "the author did not sign")
        at = body["at"]
        if at < 0:
            no("HIST.TIME", "ledger timestamps are nonnegative")
        if not genesis:
            if at < s["last_at"] or (at == s["last_at"] and POLARITY.get(kind) != "restrict"):
                no("HIST.TIME", "time runs forward (a restriction may share the last instant)")
            if kind != "checkpoint" and at > s["anchor_at"] + MAX_AHEAD_MS:
                no("HIST.AHEAD", "too far ahead of the last witnessed time")
        if body["id"] in s["statements"]:
            no("TYPE.DUPLICATE", body["id"])
        polarity = POLARITY.get(kind, "attest")
        self._gate(s, polarity, kind, root, body, signers)
        delta: list = []
        if kind in SHAPES:
            getattr(self, "_" + kind)(s, body, signers, delta)
        else:
            self._evidence(s, kind, body, signers, delta)
        if self.law.obligations:
            self._law_obligations(s, {"kind": kind, "author": body["author"], "at": at, "body": body}, delta)
        record = {"kind": kind, "polarity": polarity, "author": body["author"], "at": at, "body": body,
                  "signers": sorted(signers), "law": law.digest}
        delta += [("put", "statements", body["id"], record), ("set", "size", s["size"] + 1),
                  ("set", "head", digest(entry)), ("set", "last_at", at)]
        return record, delta

    def _law_obligations(self, s, record, d):
        label = set(self._record_label(s, record))
        opens, closes, failures = obligations.step(self.law.obligations, ("refuse",), s["obligations"], record,
                                                   lambda decl: self._holds(s, decl, record),
                                                   lambda inst: not set(inst.get("label", label)) & label)
        if failures:
            no(failures[0][1], failures[0][2])
        for name, how in closes:
            d.append(("drop", "obligations", name))
            if how == "closed":
                ob = s["obligations"][name]
                d.append(("put", "closed", name, {"type": ob["stage"], "key": ob["key"], "at": record["at"],
                                                 "label": self._record_label(s, record), "contract": ob["contract"]}))
        d.extend(("put", "obligations", name, {**inst, "label": sorted(label)}) for name, inst in opens)

    def _record_label(self, s, record):
        under = record["body"].get("under")
        return sorted({record["author"]} | ({g["holder"] for g in self._chain(s, under, record["at"])} if under else set()))

    def _holds(self, s, decl, record):
        if decl["when"] is None:
            return True
        body = record["body"]
        resource = self.law.resource_of(body["op"], body["args"]) if record["kind"] == "intent" else body.get("resource")
        facts = self._facts(s, record["author"], body.get("op"), resource, record["at"], body,
                            set(self._record_label(s, record)), decl["when"])
        try:
            return policy.evaluate(decl["when"], **facts)
        except policy.PolicyError as exc:
            no("BOUND.EXCEEDED", str(exc))

    def _signers(self, root, envelope, message) -> set:
        keys = {k["keyid"]: (ident, k) for ident, d in root["identities"].items() for k in d["keys"]}
        signers = set()
        for sig in envelope["signatures"]:
            found = keys.get(sig.get("keyid")) if isinstance(sig, dict) else None
            if found is None or not verify(found[1], message, sig):
                no("SIG.INVALID", "every signature must verify against the root in force")
            signers.add(found[0])
        return signers

    # ---- POLARITY: one gate per polarity ------------------------------------------------------------------------
    def _gate(self, s, polarity, kind, root, body, signers):
        author_kind = kind_of(root, body["author"])
        if polarity == "widen":
            if author_kind != "human":
                no("FLOOR0.HUMAN", "a widening is stated by a human of the root")
            need = root["threshold"] + (1 if body.get("override") else 0)
            got = signers & humans(root)
            if len(got) < need:
                no("FLOOR0.QUORUM", f"{need} distinct humans of the root are needed, {len(got)} signed")
        elif polarity == "restrict":
            if author_kind not in RESTRICT_BY[kind] and kind != "revoke":
                no("CAP.RESTRICT", f"{kind} is from a {' or '.join(RESTRICT_BY[kind])} of the root")
        elif polarity == "witness":
            if author_kind != "witness":
                no("CAP.WITNESS", "time is stated by witnesses")
            got = {i for i in signers if kind_of(root, i) == "witness"}
            if len(got) < self.law.witness_quorum:
                no("FLOOR0.WITNESS", f"{self.law.witness_quorum} witnesses must sign, {len(got)} signed")
        # attenuate, act, attest: the capability chain is checked by the handler

    # ---- widen: genesis, proposals, activation ------------------------------------------------------------------
    def _genesis(self, s, b, signers, d):
        if b["code"] != self.code_pin:
            no("CODE.MISMATCH", "the genesis binds another code release")
        self._witnesses_available(b["root"])
        d += [("set", "domain", digest(b)), ("set", "root", b["root"]), ("set", "root_digest", digest(b["root"])),
              ("set", "anchor_at", b["at"]), ("set", "code", b["code"]),
              ("set", "law", {"digest": self.law.digest, "client": b["law"]})]

    def _witnesses_available(self, root):
        count = sum(d["kind"] == "witness" for d in root["identities"].values())
        if count < self.law.witness_quorum:
            no("FLOOR0.WITNESS", "the root lacks enough witnesses for the law's time quorum")

    def _propose(self, s, b, signers, d, kind, extra=None):
        factor = 2 if b.get("override") else 1
        d.append(("put", "proposals", b["id"], {
            "id": b["id"], "kind": kind, "body": b, "signers": sorted(signers & humans(s["root"])),
            "not_before": b["at"] + factor * self.law.delay[kind], "override": bool(b.get("override")), "root_digest": s["root_digest"],
            "law_digest": s["law"]["digest"], **(extra or {})}))

    def _rotate(self, s, b, signers, d):
        check_root(b["root"])
        self._witnesses_available(b["root"])
        self._propose(s, b, signers, d, "rotate")

    def _grant(self, s, b, signers, d):
        self._scope(s, b)
        if b["not_after"] <= b["at"]:
            no("TYPE.SHAPE", "a grant ends after it is proposed")
        self._propose(s, b, signers, d, "grant")

    def _law(self, s, b, signers, d):
        """A new client law: composed with the floors and validated now; in force on activation."""
        try:
            new = self.load(b["release"])
        except LawError as exc:
            no("LAW.INVALID", str(exc))
        if sum(x["kind"] == "witness" for x in s["root"]["identities"].values()) < new.witness_quorum:
            no("FLOOR0.WITNESS", "the root lacks enough witnesses for the new law's time quorum")
        self._propose(s, b, signers, d, "law")

    def _unfreeze(self, s, b, signers, d):
        freeze = s["frozen"].get(b["scope"])
        if freeze is None:
            no("RESTRICT.NONE", "that scope is not frozen")
        self._propose(s, b, signers, d, "unfreeze", {"freeze": freeze})

    def _activate(self, s, b, signers, d):
        p = s["proposals"].get(b["proposal"])
        if p is None:
            no("WIDEN.UNKNOWN", "no such pending proposal (activated or never made)")
        if p["root_digest"] != s["root_digest"]:
            no("WIDEN.STALE", "the proposal was made under another root: propose again")
        if p["law_digest"] != s["law"]["digest"]:
            no("WIDEN.STALE", "the proposal was approved under another law: propose again")
        if s["anchor_at"] < p["not_before"]:
            no("WIDEN.DELAY", f"the proposal activates at {p['not_before']} of witnessed time")
        pb = p["body"]
        if p["kind"] == "law":
            d.append(("set", "law", {"digest": self.load(pb["release"]).digest, "client": pb["release"]}))
        elif p["kind"] == "rotate":
            d += [("set", "root", pb["root"]), ("set", "root_digest", digest(pb["root"]))]
        elif p["kind"] == "grant":
            if pb["not_after"] < b["at"]:
                no("WIDEN.EXPIRED", "the proposed grant has already ended")
            d.append(("put", "grants", pb["id"], self._grant_record(pb, "root", b["at"])))
        else:
            if s["frozen"].get(pb["scope"]) != p["freeze"]:
                no("WIDEN.STALE", "the scope was frozen again since: propose again")
            d.append(("drop", "frozen", pb["scope"]))
        d.append(("drop", "proposals", p["id"]))

    # ---- attenuate ------------------------------------------------------------------------------------------------
    def _scope(self, s, b):
        acts, res = b["actions"], b["resources"]
        if not acts or len(acts) > 64 or not all(isinstance(a, str) and 0 < len(a) <= 128 and "*" not in a for a in acts):
            no("TYPE.SHAPE", "actions are explicit names")
        if not res or len(res) > 64 or not all(isinstance(r, str) and PATTERN.fullmatch(r) for r in res):
            no("TYPE.SHAPE", "resources are patterns ('*' only after a separator)")
        if kind_of(s["root"], b["holder"]) is None:
            no("CAP.HOLDER", "the holder is not an identity of the root")
        if len(b["conditions"]) > 16:
            no("TYPE.SHAPE", "at most 16 conditions")
        for cond in b["conditions"]:
            self._condition(cond)
        budget = b.get("budget")
        if budget is not None and (set(budget) != {"count", "window"}
                                   or not all(type(v) is int and v > 0 for v in budget.values())):
            no("TYPE.SHAPE", "a budget is {count, window}, both positive")

    def _grant_record(self, b, parent, effective_at) -> dict:
        return {"id": b["id"], "parent": parent, "holder": b["holder"], "actions": list(b["actions"]),
                "resources": list(b["resources"]), "conditions": list(b["conditions"]), "budget": b.get("budget"),
                "not_after": b["not_after"], "effective_at": effective_at,
                "condition_digests": sorted(digest({"name": c, "policy": self.law.release["conditions"][c]}) for c in b["conditions"])}

    def _delegate(self, s, b, signers, d):
        self._scope(s, b)
        parent = self._chain(s, b["parent"], b["at"])[0]
        if b["author"] != parent["holder"]:
            no("CAP.ATTENUATE", "only the holder of a capability derives from it")
        if not set(b["actions"]) <= set(parent["actions"]) or not within(b["resources"], parent["resources"]):
            no("CAP.WIDENS", "a derived capability is included in its parent")
        record = self._grant_record(b, b["parent"], b["at"])
        if not set(parent["condition_digests"]) <= set(record["condition_digests"]) or b["not_after"] > parent["not_after"]:
            no("CAP.WIDENS", "a derived capability keeps every condition and ends no later")
        pb, cb = parent["budget"], b.get("budget")
        if pb and not (cb and cb["count"] <= pb["count"] and cb["window"] >= pb["window"]):
            no("CAP.WIDENS", "a derived capability keeps its parent's budget")
        d.append(("put", "grants", b["id"], record))

    # ---- restrict -------------------------------------------------------------------------------------------------
    def _veto(self, s, b, signers, d):
        p = s["proposals"].get(b["proposal"])
        if p is None:
            no("CAP.VETO", "nothing pending to veto")
        if p["override"]:
            no("CAP.VETO", "an override by a higher quorum cannot be vetoed")
        if b["author"] in p["signers"]:
            no("CAP.VETO", "a signer of the proposal cannot veto it")
        d.append(("drop", "proposals", p["id"]))

    def _revoke(self, s, b, signers, d):
        gid = b["grant"]
        if gid not in s["grants"]:
            no("CAP.CHAIN", "nothing to revoke")
        if kind_of(s["root"], b["author"]) != "human":
            line = set()
            while gid != "root" and gid in s["grants"]:
                line.add(s["grants"][gid]["holder"])
                gid = s["grants"][gid]["parent"]
            if b["author"] not in line:
                no("CAP.RESTRICT", "a revocation is from a human of the root or a holder along the chain")
        d.append(("put", "revoked", b["grant"], b["at"]))

    def _freeze(self, s, b, signers, d):
        d.append(("put", "frozen", b["scope"], b["id"]))

    def _flag(self, s, b, signers, d):
        if b["intent"] not in s["intents"]:
            no("CAP.FLAG", "a flag names an intent")
        d.append(("put", "flags", b["intent"], b["id"]))

    def _heartbeat(self, s, b, signers, d):
        """A declared control's signal only restores the law's default; its silence tightens (F0-5)."""
        if b["seen"] > s["size"]:
            no("CAP.HEARTBEAT", "a heartbeat is about what exists")
        d.append(("put", "heartbeats", b["author"], b["at"]))

    # ---- witness --------------------------------------------------------------------------------------------------
    def _checkpoint(self, s, b, signers, d):
        if b["size"] != s["size"] or b["head"] != s["head"]:
            no("HIST.CHECKPOINT", "a checkpoint names the current head")
        d += [("set", "anchor_at", b["at"]), ("set", "witnessed", True)]

    # ---- CAP ------------------------------------------------------------------------------------------------------
    def _condition(self, cond):
        if isinstance(cond, str):
            if cond not in self.law.conditions:
                no("LAW.CONDITION", f"unknown condition {cond}")
            return self.law.conditions[cond]
        no("LAW.CONDITION", "a condition names a policy of the sealed law")

    def _chain(self, s, gid, at) -> list:
        if gid == "root":
            no("CAP.CHAIN", "the root is not a capability: act under a grant")
        chain, seen = [], set()
        while gid != "root":
            g = s["grants"].get(gid)
            if g is None or gid in seen or len(chain) >= MAX_CHAIN:
                no("CAP.CHAIN", f"{gid} is not a capability")
            if gid in s["revoked"] or g["not_after"] < at or kind_of(s["root"], g["holder"]) is None:
                no("CAP.WITHDRAWN", f"{gid} is revoked, expired, or its holder left the root")
            if list(g["condition_digests"]) != sorted(digest({"name": c, "policy": self.law.release["conditions"].get(c)}) for c in g["conditions"]):
                no("LAW.STALE", "the capability condition changed: a new grant is required")
            chain.append(g)
            seen.add(gid)
            gid = g["parent"]
        return chain

    def _authorize(self, s, author, under, action, resource, at, stmt) -> tuple[list, list]:
        chain = self._chain(s, under, at)
        leaf = chain[0]
        if leaf["holder"] != author:
            no("CAP.HOLDER", "the author does not hold this capability")
        if action not in leaf["actions"] or not covers(leaf["resources"], resource):
            no("CAP.SCOPE", f"{action} on {resource} is outside the capability")
        label = sorted({author} | {g["holder"] for g in chain})
        if any(g["conditions"] for g in chain):
            atoms = [a for g in chain for c in g["conditions"] for a in self._condition(c)]
            facts = self._facts(s, author, action, resource, at, stmt, set(label), atoms)
            for g in chain:
                for cond in g["conditions"]:
                    try:
                        if not policy.evaluate(self._condition(cond), **facts):
                            no("LAW.CONDITION", f"a condition of {g['id']} does not hold")
                    except policy.PolicyError as exc:
                        no("BOUND.EXCEEDED", str(exc))
        return chain, label

    def _facts(self, s, author, action, resource, at, stmt, label, atoms) -> dict:
        """Facts a condition may read (F0-8): the statement itself, and only the facts its atoms name, each fresh and
        attested by a chain sharing no holder with the author's. Every fact carries a provenance label: a fact without
        one does not exist for the law, and facts nobody names cannot crowd out those that matter."""
        fresh = self.law.ttl["observation"]
        named = {op: {a[0] for o, a in atoms if o == op} for op in ("observed", "closed_at_least", "open")}
        independent = lambda f: not set(f["label"]) & label
        observed = {(o["resource"], o["property"], o["status"], o["level"]) for o in s["observations"].values()
                    if o["resource"] == resource and o["property"] in named["observed"] and o["at"] + fresh >= at and independent(o)}
        return {"request": {**stmt, "author": author, "op": stmt.get("op", action), "resource": resource}, "observations": observed,
                "opened": {(ob["stage"], ob["key"]) for ob in s["obligations"].values()
                           if ob.get("type") == "law" and ob["stage"] in named["open"] and not lapsed(ob, at) and independent(ob)},
                "closed": {(c["type"], c["key"]) for c in s["closed"].values()
                           if c["type"] in named["closed_at_least"] and c["at"] + fresh >= at and independent(c)
                           and c["contract"] == self.law.obligations.get(c["type"], {}).get("contract")}}

    def _certify(self, chain, level):
        if level not in self.law.rank:
            no("NIV.UNKNOWN", f"{level} is not a level of this law")
        if "certify:" + level not in chain[0]["actions"]:
            no("NIV.CERTIFY", f"this capability cannot certify {level}")

    def _unfrozen(self, s, resource):
        if covers(list(s["frozen"]), resource):
            no("FREEZE.ACTIVE", f"{resource} is frozen")

    def _prudent(self, s, at) -> bool:
        if not self.law.heartbeat_ms:
            return False
        sentinels = [i for i, d in s["root"]["identities"].items() if d["kind"] == "sentinel"]
        return any(at - s["heartbeats"].get(i, -10 ** 15) > self.law.heartbeat_ms for i in sentinels)

    # ---- OBL: the effect line ---------------------------------------------------------------------------------------
    def _open(self, d, name, stage, intent, at, owner):
        d.append(("put", "obligations", name, {"stage": stage, "intent": intent, "opened": at,
                                                "due": at + self.law.ttl[stage], "owner": owner}))

    def _line(self, s, d, kind, result, intent, at):
        """Advance the effect line by the one transition table of FLOOR-0; any other move is refused."""
        leave, enter = LINE[(kind, result)]
        current = line_state(s["line"], intent, at)
        if current not in leave:
            no("OBL.LINE", f"{kind} ({result}) cannot follow {current}")
        d.append(("put", "line", intent, {"state": enter, "at": at}))

    def _consume(self, s, d, name, at):
        ob = s["obligations"].get(name)
        if ob is None:
            no("OBL.NOT_OPEN", f"{name} is not open")
        if lapsed(ob, at):
            no("OBL.LAPSED", f"{name} lapsed at {ob['due']}")
        d.append(("drop", "obligations", name))

    def _intent(self, s, b, signers, d):
        op = self.law.ops.get(b["op"])
        if op is None:
            no("TYPE.OP", f"{b['op']} is not an op of this law")
        try:
            build(op["args"], b["args"], common=False)
        except ShapeError as exc:
            no("TYPE.ARGS", str(exc))
        resource = self.law.resource_of(b["op"], b["args"])
        if not RESOURCE.fullmatch(resource):
            no("TYPE.ARGS", "the arguments do not yield an exact resource")
        stmt = {**b, "resource": resource}
        _, label = self._authorize(s, b["author"], b["under"], "effect:" + b["op"], resource, b["at"], stmt)
        self._unfrozen(s, resource)
        prior = b.get("retry_of")
        if prior is not None:
            p = s["intents"].get(prior)
            if not p or (p["op"], p["resource"]) != (b["op"], resource):
                no("OBL.RETRY", "a retry names an earlier intent of the same effect")
            if self._unresolved(s, prior, b["at"]):
                no("OBL.BLOCKED", "the earlier intent is unresolved: reconcile it first")
        d.append(("put", "intents", b["id"], {"id": b["id"], "op": b["op"], "resource": resource, "args": b["args"],
                                              "author": b["author"], "under": b["under"], "label": label, "stmt": stmt, "contract": digest(op)}))
        self._line(s, d, "intent", None, b["id"], b["at"])
        self._open(d, f"pending:{b['id']}", "pending", b["id"], b["at"], b["author"])

    def _unresolved(self, s, intent_id, at) -> bool:
        names = [f"pending:{intent_id}", f"reconcile:{intent_id}"]
        if intent_id in s["token_of"]:
            names.append(f"unredeemed:{s['token_of'][intent_id]}")
        return any(n in s["obligations"] and not lapsed(s["obligations"][n], at) for n in names)

    def _reauthorize(self, s, it, at):
        if it["contract"] != digest(self.law.ops.get(it["op"])):
            no("LAW.STALE", "the operation contract changed: a new intent is required")
        chain, _ = self._authorize(s, it["author"], it["under"], "effect:" + it["op"], it["resource"], at, it["stmt"])
        self._unfrozen(s, it["resource"])
        return chain

    def _profile(self, s, it, signers, root_digest, at):
        approved = set(signers) & humans(s["root"]) if root_digest == s["root_digest"] else set()
        if self.law.ops[it["op"]]["profile"] == "human_quorum" and len(approved) < s["root"]["threshold"]:
            no("PROFILE.QUORUM", "this operation needs a human quorum of the current root")
        if (self._prudent(s, at) or it["id"] in s["flags"]) and not approved:
            no("FLOOR0.PRUDENT", "the current root must human co-sign this effect")

    def _token(self, s, b, signers, d):
        if kind_of(s["root"], b["author"]) != "guard":
            no("CAP.GUARD", "only a guard issues a token")
        it = s["intents"].get(b["intent"])
        if it is None:
            no("OBL.NOT_OPEN", "no such intent")
        self._consume(s, d, f"pending:{b['intent']}", b["at"])
        self._line(s, d, "token", None, b["intent"], b["at"])
        chain = self._reauthorize(s, it, b["at"])
        if b["args_digest"] != digest(it["args"]):
            no("OBL.MISMATCH", "the token binds other arguments than the intent")
        for g in chain:
            budget = g["budget"]
            if budget and sum(1 for t in s["uses"].get(g["id"], ()) if t > b["at"] - budget["window"]) >= budget["count"]:
                no("OBL.BUDGET", f"budget of {g['id']} spent")
        self._profile(s, it, signers, s["root_digest"], b["at"])
        d += [("put", "tokens", b["id"], {"intent": b["intent"], "guard": b["author"],
                                         "humans": sorted(signers & humans(s["root"])), "root_digest": s["root_digest"]}),
              ("put", "token_of", b["intent"], b["id"])] + [("push", "uses", g["id"], b["at"]) for g in chain]
        self._open(d, f"unredeemed:{b['id']}", "unredeemed", b["intent"], b["at"], b["author"])

    def _reservation(self, s, b, signers, d):
        tok = s["tokens"].get(b["token"])
        if tok is None or tok["guard"] != b["author"] or kind_of(s["root"], b["author"]) != "guard":
            no("CAP.GUARD", "only the issuing guard reserves the token")
        it = s["intents"][tok["intent"]]
        self._consume(s, d, f"unredeemed:{b['token']}", b["at"])
        self._line(s, d, "reservation", None, tok["intent"], b["at"])
        self._reauthorize(s, it, b["at"])
        self._profile(s, it, tok["humans"], tok["root_digest"], b["at"])
        d.append(("put", "reserved", b["token"], b["id"]))
        self._open(d, f"reconcile:{tok['intent']}", "reconcile", tok["intent"], b["at"], b["author"])

    def judge_dispatch(self, s, token_id, guard, at):
        """Pure check at the physical gate; no unsigned ledger transition."""
        self._local.law = self.law_of(s)
        tok = s["tokens"].get(token_id)
        if (tok is None or tok["guard"] != guard or kind_of(s["root"], guard) != "guard"
                or token_id not in s["reserved"] or token_id in s["executed"]):
            no("OBL.RESERVATION", "the issuing guard needs one unreported reservation")
        if at < s["last_at"] or at > s["anchor_at"] + MAX_AHEAD_MS:
            no("HIST.AHEAD", "dispatch needs current witnessed time")
        if line_state(s["line"], tok["intent"], at) != "reserved":
            no("OBL.LINE", "only a reservation still inside its dispatch window may leave")
        it = s["intents"][tok["intent"]]
        self._reauthorize(s, it, at)
        self._profile(s, it, tok["humans"], tok["root_digest"], at)
        return it

    def _execution(self, s, b, signers, d):
        tok = s["tokens"].get(b["token"])
        if tok is None or tok["guard"] != b["author"]:
            no("CAP.GUARD", "the guard that issued the token reports its execution")
        if b["token"] not in s["reserved"] or b["token"] in s["executed"]:
            no("OBL.RESERVATION", "exactly one unreported reservation must precede the result")
        if b["result"] not in ("ok", "failed", "unknown"):
            no("TYPE.SHAPE", "result is ok, failed or unknown")
        d.append(("put", "executed", b["token"], b["result"]))
        intent = tok["intent"]
        self._line(s, d, "execution", b["result"], intent, b["at"])
        if b["result"] in ("ok", "failed"):
            self._consume(s, d, f"reconcile:{intent}", b["at"])
        if b["result"] == "ok":
            self._open(d, f"proof:{intent}", "proof", intent, b["at"], b["author"])

    # ---- attest -----------------------------------------------------------------------------------------------------
    def _independent(self, label, it):
        if set(label) & set(it["label"]):
            no("PROV.NOT_INDEPENDENT", "the attestation shares a holder with the actor's chain")

    def _reconciliation(self, s, b, signers, d):
        it = s["intents"].get(b["intent"])
        if it is None:
            no("OBL.NOT_OPEN", "no such intent")
        _, label = self._authorize(s, b["author"], b["under"], "reconcile", it["resource"], b["at"], b)
        self._independent(label, it)
        if b["result"] not in ("applied", "not_applied"):
            no("TYPE.SHAPE", "result is applied or not_applied")
        self._line(s, d, "reconciliation", b["result"], b["intent"], b["at"])
        self._consume(s, d, f"reconcile:{b['intent']}", b["at"])
        if b["result"] == "applied":
            self._open(d, f"proof:{b['intent']}", "proof", b["intent"], b["at"], b["author"])

    def _observation(self, s, b, signers, d):
        chain, label = self._authorize(s, b["author"], b["under"], "observe", b["resource"], b["at"], b)
        self._certify(chain, b["level"])
        d.append(("put", "observations", f"{b['resource']}|{b['property']}|{b['author']}",
                  {"id": b["id"], "resource": b["resource"], "property": b["property"], "status": b["status"],
                   "level": b["level"], "at": b["at"], "author": b["author"], "label": label}))

    def _evidence(self, s, kind, b, signers, d):
        chain, label = self._authorize(s, b["author"], b["under"], kind, b["resource"], b["at"], b)
        if "level" in b:
            self._certify(chain, b["level"])
        for rule in self.law.discharges.get(kind, []):
            target = b[rule["key"]]
            it = s["intents"].get(target)
            if it is None or it["resource"] != b["resource"]:
                no("PROV.SUBJECT", "the proof must name an intent on this exact resource")
            if self.law.rank[b["level"]] < self.law.rank[rule["min_level"]]:
                no("NIV.TOO_LOW", f"proof:{target} needs {rule['min_level']}")
            self._independent(label, it)
            self._consume(s, d, f"proof:{target}", b["at"])
