"""F0-2: a second check of named critical transitions at the journal boundary.

The kernel decides (record, delta). This module reads the signed entry itself, checks the cryptographic signature
through a separate path, and compares the state change to it. It also checks invariant restrictions; it does not
independently interpret every part of the law. A disagreement is a refusal and a persistent local halt.

It covers the properties whose failure would be unrecoverable: who may touch which part of the state (polarity),
widening only through an activated proposal under the current quorum, attenuation, single use of tokens, the
obligation line, witnessed time and the shape of every root."""
from __future__ import annotations

import base64
import hashlib
import json
import copy
from collections.abc import Mapping

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from .canon import canon, digest, parse
from .floor0 import LINE, line_state
from .floors import floors_digest


class Disagreement(Exception):
    pass


BOOK = {("put", "statements"), ("set", "size"), ("set", "head"), ("set", "last_at")}
TOUCH = {
    "genesis": {("set", "domain"), ("set", "root"), ("set", "root_digest"), ("set", "anchor_at"), ("set", "code"),
                ("set", "law")},
    "rotate": {("put", "proposals")}, "grant": {("put", "proposals")}, "unfreeze": {("put", "proposals")},
    "law": {("put", "proposals")},
    "activate": {("set", "root"), ("set", "root_digest"), ("set", "law"), ("put", "grants"), ("drop", "frozen"),
                 ("drop", "proposals")},
    "delegate": {("put", "grants")}, "veto": {("drop", "proposals")},
    "revoke": {("put", "revoked")}, "freeze": {("put", "frozen")},
    "flag": {("put", "flags")}, "heartbeat": {("put", "heartbeats")},
    "checkpoint": {("set", "anchor_at"), ("set", "witnessed")},
    "intent": {("put", "intents"), ("put", "obligations"), ("put", "line")},
    "token": {("drop", "obligations"), ("put", "tokens"), ("put", "token_of"), ("push", "uses"), ("put", "obligations"),
              ("put", "line")},
    "reservation": {("drop", "obligations"), ("put", "reserved"), ("put", "obligations"), ("put", "line")},
    "execution": {("put", "executed"), ("drop", "obligations"), ("put", "obligations"), ("put", "line")},
    "reconciliation": {("drop", "obligations"), ("put", "obligations"), ("put", "line")},
    "observation": {("put", "observations")},
}
EVIDENCE = {("drop", "obligations")}
RESTRICT_KINDS = {"veto", "revoke", "freeze", "flag", "heartbeat"}       # restated apart from floor0.POLARITY


HANDLERS = {"genesis": "_genesis", "rotate": "_rotate", "grant": "_grant", "unfreeze": "_unfreeze", "law": "_law_entry",
            "activate": "_activate", "delegate": "_delegate", "veto": "_veto", "checkpoint": "_checkpoint",
            "intent": "_intent", "token": "_token", "reservation": "_reservation", "execution": "_execution"}


def _no(why: str):
    raise Disagreement(why)


def _humans(root) -> set:
    return {i for i, d in root["identities"].items() if d.get("kind") == "human"}


def _kinds(root, names, kind) -> set:
    return {n for n in names if root["identities"].get(n, {}).get("kind") == kind}


def _inside(child: str, parent: str) -> bool:
    """Pattern inclusion, written apart from shapes.py: '*' only ends a pattern."""
    if parent == child:
        return True
    if not parent.endswith("*"):
        return False
    stem = parent[:-1]
    return (child[:-1] if child.endswith("*") else child).startswith(stem)


def _grant(body, parent, at, conditions):
    return {"id": body["id"], "parent": parent, "holder": body["holder"],
            "actions": list(body["actions"]), "resources": list(body["resources"]),
            "conditions": list(body["conditions"]), "budget": body.get("budget"),
            "not_after": body["not_after"], "effective_at": at,
            "condition_digests": sorted(digest({"name": c, "policy": conditions[c]}) for c in body["conditions"])}


def _root_ok(root, witness_quorum: int) -> None:
    humans, k = _humans(root), root.get("threshold")
    if type(k) is not int or k < 2 or len(humans) < k + 2:
        _no("a root needs a quorum of at least 2 and two additional humans")
    if len(_kinds(root, root["identities"], "witness")) < witness_quorum:
        _no("a root keeps enough witnesses for the time quorum")


class Invariants:
    """`law` is the effective law the kernel says it judged under; `check` first confirms it is the law in force."""

    def _use(self, law):
        # Independent snapshot from pinned declarations, never mutable kernel-derived fields.
        if getattr(self, "_digest", None) == law.digest:
            return
        raw = copy.deepcopy(law.release)
        if digest(raw) != law.digest:
            _no("the law snapshot differs from its pin")
        self.witness_quorum, self.evidence = raw["witnesses"]["quorum"], set(raw["evidence"])
        self.delay, self.ops, self.fresh = raw["delays"], raw["ops"], raw["ttl"]["observation"]
        self.raw_conditions = raw["conditions"]
        self.conditions = {n: [(next(iter(a)), next(iter(a.values()))) for a in d["all"]]
                           for n, d in self.raw_conditions.items()}
        self.decls = [{**d, **{k: [{"where": {}, "op": None, **r} for r in d.get(k, [])]
                              for k in ("gate", "open", "close")}}
                      for d in raw["obligations"] if d["level"] == "refuse"]
        self.contracts = {d["id"]: digest(d) for d in raw["obligations"]}
        self.law_types, self._digest = {d["id"] for d in self.decls}, law.digest

    def _is_law(self, op) -> bool:
        return (op[1] in ("obligations", "closed") and op[0] in ("put", "drop")
                and op[2].split(":", 1)[0] in self.law_types)

    def check(self, pre: dict, record: dict, delta: list, entry: dict, law) -> None:
        if record.get("law") != law.digest or (pre["size"] and pre["law"]["digest"] != law.digest):
            _no("an entry is judged under the law in force at its position")
        self._use(law)
        self._signed(pre, record, entry)
        entry_digest = digest(entry)
        kind, body, at = record["kind"], record["body"], record["at"]
        allowed = EVIDENCE if kind in self.evidence else TOUCH.get(kind)
        if allowed is None:
            _no(f"unknown kind {kind}")
        law_ops = [op for op in delta if self._is_law(op)]
        delta = [op for op in delta if not self._is_law(op)]
        ops = [(op[0], op[1]) for op in delta]
        for op in ops:
            if op not in allowed and op not in BOOK:
                _no(f"{kind} may not {op[0]} {op[1]}")
        book = [op for op in delta if (op[0], op[1]) in BOOK]
        if sorted((o[0], o[1]) for o in book) != sorted(BOOK):
            _no("every entry records itself exactly once")
        values = {(o[0], o[1]): o for o in book}
        if values[("set", "size")][2] != pre["size"] + 1 or values[("set", "head")][2] != entry_digest:
            _no("an entry extends the head by one")
        if values[("put", "statements")][2:] != (body["id"], record):
            _no("the signed statement must be recorded unchanged")
        if values[("set", "last_at")][2] != at or pre["size"] and (
                at < pre["last_at"] or at == pre["last_at"] and kind not in RESTRICT_KINDS):
            _no("time runs forward; only a restriction shares the last instant")
        if (kind == "genesis") != (pre["size"] == 0):
            _no("genesis is first and only first")
        root = body["root"] if kind == "genesis" else pre["root"]
        if any(name not in root["identities"] for name in record["signers"]) or record["author"] not in record["signers"]:
            _no("every signer is an identity of the root in force, and the author signed")
        signers = set(record["signers"])
        handler = HANDLERS.get(kind) if kind not in self.evidence else None
        if handler is not None:
            getattr(self, handler)(pre, record, delta, root, signers)
        self._obligations(pre, record, delta)
        self._line(pre, record, delta)
        self._law(pre, record, law_ops)

    def _line(self, pre, record, delta):
        """The effect line moves exactly along the FLOOR-0 table, once per effect entry, and nowhere else."""
        kind, body, at = record["kind"], record["body"], record["at"]
        moves = [op for op in delta if op[:2] == ("put", "line")]
        if kind not in ("intent", "token", "reservation", "execution", "reconciliation"):
            return
        intent = {"intent": body["id"], "token": body.get("intent"), "reconciliation": body.get("intent")}.get(
            kind) or pre["tokens"].get(body.get("token"), {}).get("intent")
        leave, enter = LINE.get((kind, body.get("result")), ((), None))
        if (line_state(pre.get("line", {}), intent, at) not in leave
                or moves != [("put", "line", intent, {"state": enter, "at": at})]):
            _no(f"{kind} moves the effect line outside its table")

    def _signed(self, pre, record, entry):
        """Read the actual envelope, including every signature, independently of the kernel's record."""
        try:
            if set(entry) != {"seq", "prev", "envelope"} or entry["seq"] != pre["size"] or entry["prev"] != pre["head"]:
                _no("signed entry does not extend the previous head")
            env = entry["envelope"]
            if set(env) != {"payloadType", "payload", "signatures"} or env["payloadType"] != "application/vnd.in-toto+json":
                _no("the envelope carries exactly a payload type, a payload and signatures")
            ids = [s["keyid"] for s in env["signatures"]]
            if ids != sorted(set(ids)) or any(set(s) - {"keyid", "sig", "webauthn"} for s in env["signatures"]):
                _no("one signature per key, in key order, nothing unsigned beside them")
            payload = base64.b64decode(env["payload"], validate=True)
            st = parse(payload)
            body = st["predicate"]
            kind = st["predicateType"].removeprefix("urn:standard:tcb:1:")
            root = body["root"] if pre["size"] == 0 else pre["root"]
            domain = "genesis" if pre["size"] == 0 else pre["domain"]
            expected = {"_type": "https://in-toto.io/Statement/v1", "predicateType": "urn:standard:tcb:1:" + kind,
                        "predicate": body, "subject": [{"name": f"{domain}/{kind}:{body['id']}",
                        "digest": {"sha256": hashlib.sha256(canon(body)).hexdigest()}}]}
            if st != expected or record["kind"] != kind or record["body"] != body or record["at"] != body["at"] or record["author"] != body["author"]:
                _no("the kernel record differs from the signed statement")
            message = b"DSSEv1 %d %s %d %s" % (len(env["payloadType"]), env["payloadType"].encode(), len(payload), payload)
            keys = {k["keyid"]: (name, k) for name, ident in root["identities"].items() for k in ident["keys"]}
            signers = set()
            for signature in env["signatures"]:
                name, key = keys[signature["keyid"]]
                public = base64.b64decode(key["public"], validate=True)
                if "sha256:" + hashlib.sha256(public).hexdigest() != signature["keyid"]:
                    _no("the signer key id is incorrect")
                if key["alg"] == "ed25519":
                    Ed25519PublicKey.from_public_bytes(public).verify(base64.b64decode(signature["sig"], validate=True), message)
                elif key["alg"] == "webauthn-es256":
                    w = signature["webauthn"]
                    auth = base64.urlsafe_b64decode(w["authenticatorData"] + "=" * (-len(w["authenticatorData"]) % 4))
                    client_raw = base64.urlsafe_b64decode(w["clientDataJSON"] + "=" * (-len(w["clientDataJSON"]) % 4))
                    client = json.loads(client_raw)
                    challenge = base64.urlsafe_b64encode(hashlib.sha256(message).digest()).rstrip(b"=").decode()
                    if (client.get("type") != "webauthn.get" or client.get("origin") not in key["origins"]
                            or client.get("challenge") != challenge or len(auth) < 37
                            or auth[:32] != hashlib.sha256(key["rp_id"].encode()).digest() or auth[32] & 0x05 != 0x05):
                        _no("WebAuthn assertion is invalid")
                    sig = base64.urlsafe_b64decode(signature["sig"] + "=" * (-len(signature["sig"]) % 4))
                    ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), public).verify(
                        sig, auth + hashlib.sha256(client_raw).digest(), ec.ECDSA(hashes.SHA256()))
                else:
                    _no("unknown signature algorithm")
                signers.add(name)
            if not signers or body["author"] not in signers or sorted(signers) != record["signers"]:
                _no("record signers differ from verified signatures")
        except Disagreement:
            raise
        except Exception as exc:
            _no("cannot independently verify the signed entry: " + type(exc).__name__)

    # ---- widening ------------------------------------------------------------------------------------------------
    def _quorum(self, root, signers, extra=0):
        if len(signers & _humans(root)) < root["threshold"] + extra:
            _no("a widening carries the quorum of the root in force")

    def _genesis(self, pre, record, delta, root, signers):
        _root_ok(root, self.witness_quorum)
        self._quorum(root, signers)
        body = record["body"]
        expected = {("set", "domain", digest(body)), ("set", "root_digest", digest(root)),
                    ("set", "anchor_at", record["at"]), ("set", "code", body["code"])}
        if not expected <= {tuple(op) for op in delta if op[0] == "set" and op[1] not in ("root", "law")} or ("set", "root", root) not in delta:
            _no("genesis state must equal its signed body")
        if [op[2] for op in delta if op[:2] == ("set", "law")] != [{"digest": record["law"], "client": body["law"]}]:
            _no("the genesis puts exactly its own client law in force")

    def _proposal(self, pre, record, delta, signers):
        body, kind = record["body"], record["kind"]
        expected = {"id": body["id"], "kind": kind, "body": body,
                    "signers": sorted(signers & _humans(pre["root"])),
                    "not_before": body["at"] + (2 if body.get("override") else 1) * self.delay[kind],
                    "override": bool(body.get("override")), "root_digest": pre["root_digest"],
                    "law_digest": pre["law"]["digest"]}
        if kind == "unfreeze":
            expected["freeze"] = pre["frozen"].get(body["scope"])
        if ("put", "proposals", body["id"], expected) not in delta:
            _no("the proposed rights and delay must equal the signed request")

    def _rotate(self, pre, record, delta, root, signers):
        _root_ok(record["body"]["root"], self.witness_quorum)
        self._quorum(root, signers, 1 if record["body"].get("override") else 0)
        self._proposal(pre, record, delta, signers)

    def _grant(self, pre, record, delta, root, signers):
        self._quorum(root, signers, 1 if record["body"].get("override") else 0)
        self._proposal(pre, record, delta, signers)

    _unfreeze = _grant

    def _law_entry(self, pre, record, delta, root, signers):
        release = record["body"]["release"]
        if not isinstance(release, Mapping) or release.get("floors") != floors_digest():
            _no("a client law is written for the floors of this release")
        self._grant(pre, record, delta, root, signers)

    def _activate(self, pre, record, delta, root, signers):
        self._quorum(root, signers)
        p = pre["proposals"].get(record["body"]["proposal"])
        if p is None or p["root_digest"] != pre["root_digest"] or p["law_digest"] != pre["law"]["digest"] or pre["anchor_at"] < p["not_before"]:
            _no("activation needs a live proposal of this root whose witnessed delay has passed")
        for op in delta:
            if op[:2] == ("set", "root"):
                if p["kind"] != "rotate" or op[2] != p["body"]["root"]:
                    _no("only an activated rotation replaces the root, with exactly the proposed root")
                _root_ok(op[2], self.witness_quorum)
            elif op[:2] == ("set", "root_digest") and op[2] != digest(p["body"]["root"]):
                _no("the activated root digest must equal its signed root")
            elif op[:2] == ("put", "grants"):
                if p["kind"] != "grant" or op[2] != p["id"] or op[3] != _grant(p["body"], "root", record["at"], self.raw_conditions):
                    _no("an activated grant must equal its signed proposal")
            elif op[:2] == ("drop", "frozen") and (p["kind"] != "unfreeze" or op[2] != p["body"]["scope"]):
                _no("only an activated unfreeze lifts exactly its scope")
            elif op[:2] == ("set", "law") and (p["kind"] != "law" or p.get("law_digest") != pre["law"]["digest"]
                                                or op[2].get("client") != p["body"]["release"]):
                _no("only an activated law proposal of the law in force replaces the client law, with exactly its text")

    # ---- attenuation and restriction -----------------------------------------------------------------------------
    def _delegate(self, pre, record, delta, root, signers):
        for op in delta:
            if op[:2] != ("put", "grants"):
                continue
            child, parent = op[3], pre["grants"].get(op[3]["parent"])
            if child != _grant(record["body"], record["body"]["parent"], record["at"], self.raw_conditions) or op[2] != record["body"]["id"]:
                _no("delegated rights must equal the signed scope")
            if parent is None or child["parent"] == "root" or record["author"] != parent["holder"]:
                _no("a delegation derives from a grant its author holds")
            if (not set(child["actions"]) <= set(parent["actions"])
                    or not all(any(_inside(c, p) for p in parent["resources"]) for c in child["resources"])
                    or child["not_after"] > parent["not_after"]
                    or not set(parent["condition_digests"]) <= set(child["condition_digests"])):
                _no("a delegation never widens its parent")
            pb, cb = parent.get("budget"), child.get("budget")
            if pb and not (cb and cb["count"] <= pb["count"] and cb["window"] >= pb["window"]):
                _no("a delegation keeps its parent's budget")
            if op[2] in pre["grants"]:
                _no("a grant identity is never reused")

    def _veto(self, pre, record, delta, root, signers):
        p = pre["proposals"].get(record["body"]["proposal"])
        if (p is None or p["override"] or record["author"] in p["signers"]
                or root["identities"][record["author"]]["kind"] != "human"
                or ("drop", "proposals", p["id"]) not in delta):
            _no("only a non-signing human vetoes a pending ordinary proposal")

    def _checkpoint(self, pre, record, delta, root, signers):
        if len(_kinds(root, signers, "witness")) < self.witness_quorum:
            _no("time moves only with the witness quorum")
        body = record["body"]
        if body["size"] != pre["size"] or body["head"] != pre["head"]:
            _no("a checkpoint names the current head")
        if ("set", "anchor_at", record["at"]) not in delta or ("set", "witnessed", True) not in delta:
            _no("witnessed time must equal the signed checkpoint")

    # ---- the effect line -------------------------------------------------------------------------------------------
    def _authority(self, pre, it, at):
        chain, seen, gid = [], set(), it["under"]
        while gid != "root":
            if gid in seen or len(seen) >= 16 or gid not in pre["grants"]:
                _no("invalid effect capability chain")
            grant = pre["grants"][gid]
            if gid in pre["revoked"] or grant["not_after"] < at or grant["holder"] not in pre["root"]["identities"]:
                _no("effect capability withdrawn")
            if list(grant["condition_digests"]) != sorted(digest({"name": c, "policy": self.raw_conditions.get(c)}) for c in grant["conditions"]):
                _no("effect capability conditions have changed")
            seen.add(gid)
            chain.append(grant)
            gid = grant["parent"]
        if (not chain or chain[0]["holder"] != it["author"] or "effect:" + it["op"] not in chain[0]["actions"]
                or not any(_inside(it["resource"], r) for r in chain[0]["resources"])):
            _no("effect outside the actor's capability")
        if any(_inside(it["resource"], r) for r in pre["frozen"]):
            _no("effect resource frozen")
        labels = {it["author"], *(g["holder"] for g in chain)}
        observations = {(o["resource"], o["property"], o["status"], o["level"]) for o in pre["observations"].values()
                        if o["at"] + self.fresh >= at and not labels.intersection(o["label"])}
        closed = {(c["type"], c["key"]) for c in pre["closed"].values()
                  if c["at"] + self.fresh >= at and not labels.intersection(c["label"])
                  and c["contract"] == self.contracts.get(c["type"])}
        opened = {(o["stage"], o["key"]) for o in pre["obligations"].values() if o.get("type") == "law" and _alive(o, at)
                  and o.get("label") is not None and not labels.intersection(o["label"])}
        for grant in chain:
            for name in grant["conditions"]:
                for op, args in self.conditions[name]:
                    value = it["stmt"]
                    if op in ("eq", "prefix", "open"):
                        for part in args[1 if op == "open" else 0].split("."):
                            value = value.get(part) if isinstance(value, Mapping) else None
                    if op == "eq":
                        ok = type(value) is type(args[1]) and value == args[1]
                    elif op == "prefix":
                        ok = isinstance(value, str) and value.startswith(args[1])
                    elif op == "observed":
                        ok = (it["resource"], *args) in observations
                    elif op == "closed_at_least":
                        ok = len({key for kind, key in closed if kind == args[0]}) >= args[1]
                    elif op == "open":
                        ok = (args[0], value) in opened
                    else:
                        ok = False
                    if not ok:
                        _no("effect policy does not hold")

    def _intent(self, pre, record, delta, root, signers):
        body = record["body"]
        it = next(op[3] for op in delta if op[:2] == ("put", "intents"))
        resource = self.ops[body["op"]]["resource"].format(**body["args"])
        if (any(it[k] != body[k] for k in ("id", "op", "args", "author", "under"))
                or it["resource"] != resource or it["stmt"] != {**body, "resource": resource}
                or it["contract"] != digest(self.ops[body["op"]])):
            _no("stored effect differs from the signed request")
        self._authority(pre, it, record["at"])

    def _profile(self, pre, it, token):
        approved = set(token["humans"]) & _humans(pre["root"]) if token["root_digest"] == pre["root_digest"] else set()
        if self.ops[it["op"]]["profile"] == "human_quorum" and len(approved) < pre["root"]["threshold"]:
            _no("sensitive effect lacks the current human quorum")

    def dispatch(self, pre, token, at, law):
        if pre["law"]["digest"] != law.digest:
            _no("dispatch is judged under the law in force")
        self._use(law)
        tok = pre["tokens"][token]
        if line_state(pre.get("line", {}), tok["intent"], at) != "reserved":
            _no("only a reservation inside its dispatch window may leave")
        it = pre["intents"][tok["intent"]]
        if it["contract"] != digest(self.ops.get(it["op"])):
            _no("effect operation contract has changed")
        self._authority(pre, it, at)
        self._profile(pre, it, tok)
        return {"op": it["op"], "resource": it["resource"], "args": copy.deepcopy(it["args"])}

    def _token(self, pre, record, delta, root, signers):
        if root["identities"].get(record["author"], {}).get("kind") != "guard":
            _no("only a guard issues tokens")
        if record["body"]["intent"] in pre["token_of"]:
            _no("an intent has at most one token")
        tok = next(op[3] for op in delta if op[:2] == ("put", "tokens"))
        if tok["humans"] != sorted(signers & _humans(root)) or tok["root_digest"] != pre["root_digest"]:
            _no("human approvals must equal the verified signatures")
        self._profile(pre, pre["intents"][record["body"]["intent"]], tok)

    def _reservation(self, pre, record, delta, root, signers):
        token = record["body"]["token"]
        tok = pre["tokens"].get(token)
        if tok is None or tok["guard"] != record["author"] or token in pre["reserved"]:
            _no("a token is reserved once, by the guard that issued it")
        ob = pre["obligations"].get(f"unredeemed:{token}")
        if ob is None or record["at"] > ob["due"]:
            _no("a reservation consumes a live unredeemed token")
        self._profile(pre, pre["intents"][tok["intent"]], tok)

    def _execution(self, pre, record, delta, root, signers):
        token = record["body"]["token"]
        if token not in pre["reserved"] or token in pre["executed"]:
            _no("an execution reports one reserved token, once")

    def _obligations(self, pre, record, delta):
        """The obligation line: which names an entry may consume and open."""
        kind, body = record["kind"], record["body"]
        intent_of_token = lambda t: pre["tokens"].get(t, {}).get("intent")
        consume = {"token": {f"pending:{body.get('intent')}"},
                   "reservation": {f"unredeemed:{body.get('token')}"},
                   "execution": {f"reconcile:{intent_of_token(body.get('token'))}"},
                   "reconciliation": {f"reconcile:{body.get('intent')}"}}.get(kind)
        open_ = {"intent": {f"pending:{body['id']}"}, "token": {f"unredeemed:{body['id']}"},
                 "reservation": {f"reconcile:{intent_of_token(body.get('token'))}"},
                 "execution": {f"proof:{intent_of_token(body.get('token'))}"},
                 "reconciliation": {f"proof:{body.get('intent')}"}}.get(kind, set())
        if kind in self.evidence:
            consume = {name for op in delta if op[:2] == ("drop", "obligations") for name in [op[2]] if name.startswith("proof:")}
        for op in delta:
            if op[:2] == ("drop", "obligations"):
                if op[2] not in (consume or set()) or op[2] not in pre["obligations"]:
                    _no(f"{kind} may not consume {op[2]}")
            elif op[:2] == ("put", "obligations"):
                if op[2] not in open_ or op[2] in pre["obligations"]:
                    _no(f"{kind} may not open {op[2]}")


def _key(rule, record):
    """Written apart from obligations.key_of: the key an entry designates under a declared rule."""
    body = record["body"]
    if record["kind"] != rule["kind"] or (rule["op"] is not None and body.get("op") != rule["op"]):
        return None
    def at(path):
        value = body
        for part in path.split("."):
            value = value.get(part) if isinstance(value, dict) else None
        return value
    for path, expected in rule["where"].items():
        if at(path) != expected or type(at(path)) is not type(expected):
            return None
    value = at(rule["key"])
    return value if type(value) in (str, int) else None


def _alive(ob, at) -> bool:
    return not (ob.get("on_due") == "lapse" and at > ob["due"])


def _label(pre, record):
    holders, seen = {record["author"]}, set()
    gid = record["body"].get("under", "root")
    while gid != "root":
        if gid in seen or len(seen) >= 16 or gid not in pre["grants"]:
            _no("invalid provenance chain of the closure")
        seen.add(gid)
        grant = pre["grants"][gid]
        holders.add(grant["holder"])
        gid = grant["parent"]
    return sorted(holders)


def _law(self, pre, record, ops):
    """Refuse-level law obligations: re-derive which instances this entry may open, close or needs open."""
    may_open, may_close, may_satisfy = set(), set(), set()
    for d in self.decls:
        for rule in d["gate"]:
            k = _key(rule, record)
            inst = pre["obligations"].get(f"{d['id']}:{k}")
            if k is not None and not (inst and _alive(inst, record["at"]) and inst.get("label") is not None
                                      and not set(inst["label"]) & set(_label(pre, record))):
                _no(f"{record['kind']} passed a closed gate {d['id']}:{k}")
        for rule in d["open"]:
            k = _key(rule, record)
            if k is not None:
                may_open.add(f"{d['id']}:{k}")
                may_close.add(f"{d['id']}:{k}")           # replacement of the same key
        for rule in d["close"]:
            k = _key(rule, record)
            if k is not None:
                may_close.add(f"{d['id']}:{k}")
                may_satisfy.add(f"{d['id']}:{k}")
    dropped = {op[2] for op in ops if op[:2] == ("drop", "obligations")}
    for op in ops:
        name = op[2]
        if op[:2] == ("put", "obligations") and (name not in may_open or op[3]["due"] <= op[3]["opened"]
                                                    or op[3].get("label") != _label(pre, record)
                                                    or op[3]["stage"] != name.split(":", 1)[0]
                                                    or op[3].get("contract") != self.contracts.get(name.split(":", 1)[0])):
            _no(f"{record['kind']} may not open {name}")
        if op[:2] == ("drop", "obligations") and (name not in may_close or name not in pre["obligations"]):
            _no(f"{record['kind']} may not close {name}")
        if op[:2] == ("put", "closed"):
            previous = pre["obligations"].get(name)
            if (name not in may_satisfy or name not in dropped or previous is None or not _alive(previous, record["at"])
                    or op[3] != {"type": previous["stage"], "key": previous["key"], "at": record["at"],
                                 "label": _label(pre, record), "contract": previous["contract"]}
                    or previous["contract"] != self.contracts.get(previous["stage"])):
                _no(f"{record['kind']} may not record {name} as closed")


Invariants._law = _law


def check_entry(invariants: Invariants, pre: dict, record: dict, delta: list, entry: dict) -> None:
    invariants.check(pre, record, delta, entry)
