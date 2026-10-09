"""A small world for the probes: four humans (quorum 2), an agent, two oracles, a guard, two witnesses (quorum 2),
a sentinel, and a law with one typed op `merge(pr: segment, method: str) -> repo:pr:{pr}`."""
from __future__ import annotations

import base64
import copy
import re
import sys
import tempfile
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tcb import Accountability, Auditor, EffectPort, Guard, Journal, Kernel, Refused, SQLitePins, entry  # noqa: E402
from tcb.canon import digest  # noqa: E402
from tcb.crypto import keyid  # noqa: E402
from tcb.floor0 import MAX_AHEAD_MS, floor0_digest  # noqa: E402
from tcb.floors import FLOORS, floors_digest  # noqa: E402
from tcb.sign import envelope  # noqa: E402

T0 = 1_790_000_000_000
MIN = 60_000
H = 3_600_000
DAY = 86_400_000
ROLES = {"alice": "human", "bob": "human", "carol": "human", "dave": "human", "agent": "agent", "readback": "oracle", "ci": "oracle",
         "guard": "guard", "w1": "witness", "w2": "witness", "sentinel": "sentinel"}


def public(key) -> str:
    return base64.b64encode(key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)).decode()


def identity(kind, key) -> dict:
    p = public(key)
    return {"kind": kind, "keys": [{"alg": "ed25519", "public": p, "keyid": keyid(p)}]}


def make_law(fresh_ms=DAY, due_ms=DAY, heartbeat_ms=0, owner="alice", **over) -> dict:
    """A client law: it binds the floor roles, adds one target of its own, and may only tighten the floors."""
    law = {"format": "standard-client/1", "floors": floors_digest(),
           "bindings": {"owner": owner, "inventory_source": "ci", "scanner": "ci", "compliance_officer": "carol"},
           "targets": [{"id": "pr42-ci", "kind": "property", "coverage": "inventory", "resource": "repo:pr:42",
                        "property": "ci", "expect": "green", "min_level": "real", "fresh_ms": fresh_ms,
                        "due_ms": due_ms, "owner": owner, "sources": ["ci"], "repair": "merge"}]}
    if (fresh_ms, due_ms) != (DAY, DAY):
        law["tighten"] = {"targets": {"inventory": {"fresh_ms": fresh_ms, "due_ms": due_ms}}}
    if heartbeat_ms:
        law["controls"] = {"heartbeat_ms": heartbeat_ms}
    law.update(over)
    return law


class World:
    def __init__(self, law=None, tmp=None, roles=None, genesis=True):
        self.tmp = Path(tmp or tempfile.mkdtemp())
        self.roles = dict(roles or ROLES)
        self.keys = {n: Ed25519PrivateKey.generate() for n in self.roles}
        self.root = {"threshold": 2, "identities": {n: identity(r, self.keys[n]) for n, r in self.roles.items()}}
        self.law = law or make_law()
        self.kernel = Kernel()
        self.acc = Accountability(self.kernel)
        self.path = self.tmp / "journal.sqlite3"
        self.pins = SQLitePins(self.tmp / "pins.sqlite3", create=True)
        self.journal = Journal(self.path, self.kernel, checkpoints=self.pins, accountability=Auditor())
        self.n = 0
        if genesis:
            self.gid = self.add("genesis", "alice", T0, ["alice", "bob"], root=self.root, law=self.law)
            self.journal.genesis_pin = self.state["domain"]
            self.pins.bind(self.journal.genesis_pin)
            self.pins.retain({"size": self.state["size"], "head": self.state["head"]})

    @property
    def state(self):
        return self.journal.snapshot()

    def signed(self, kind, author, at, signers=None, keys=None, state=None, **fields):
        self.n += 1
        s = state or self.state
        keys = keys or self.keys
        if kind == "genesis":
            fields.setdefault("code", self.kernel.code_pin)
        body = {"id": f"{kind}-{self.n}", "at": at, "author": author, **fields}
        env = envelope("genesis" if kind == "genesis" else s["domain"], kind, body,
                       [(keyid(public(keys[x])), keys[x]) for x in (signers or [author])])
        return entry(s["size"], s["head"], env), body["id"]

    def add(self, kind, author, at, signers=None, keys=None, **fields) -> str:
        e, ident = self.signed(kind, author, at, signers, keys, **fields)
        self.journal.append(e)
        return ident

    def refuse(self, expected_code, kind, author, at, signers=None, keys=None, **fields) -> str:
        e, _ = self.signed(kind, author, at, signers, keys, **fields)
        try:
            self.journal.append(e)
        except Refused as r:
            assert r.code == expected_code, f"expected {expected_code}, got {r.code}: {r.detail}"
            return r.detail
        raise AssertionError(f"expected refusal {expected_code}, but {kind} was admitted")

    def tick(self, at) -> str:
        """Witnessed time: both witnesses sign a checkpoint of the current head."""
        s = self.state
        return self.add("checkpoint", "w1", at, ["w1", "w2"], size=s["size"], head=s["head"])

    def widen(self, kind, at, signers=("alice", "bob"), **fields) -> tuple[str, int]:
        """Propose, wait for witnessed time, activate. Returns (proposal id, time after activation)."""
        pid = self.add(kind, signers[0], at, list(signers), **fields)
        t = at + (2 if fields.get("override") else 1) * self.kernel.law_of(self.state).delay[kind]
        self.tick(t)
        self.add("activate", signers[0], t + 1, list(signers), proposal=pid)
        return pid, t + 2

    def grant(self, holder, actions, resources, at, conditions=(), budget=None, not_after=None):
        fields = {"holder": holder, "actions": actions, "resources": resources, "conditions": list(conditions),
                  "not_after": not_after or at + 30 * DAY}
        if budget:
            fields["budget"] = budget
        return self.widen("grant", at, **fields)

    def guard(self, executor, journal=None):
        port = EffectPort({op: (lambda o: lambda resource, args, reservation_key: executor(o, resource, args))(op)
                           for op in ("merge", "fix", "release")})
        return Guard(journal or self.journal, "guard", (keyid(public(self.keys["guard"])), self.keys["guard"]), port)

    def cosigner(self, name):
        return (keyid(public(self.keys[name])), self.keys[name])

    def other_journal(self):
        return Journal(self.path, self.kernel, genesis_pin=self.journal.genesis_pin,
                       checkpoints=self.pins, accountability=Auditor())


class raises:
    def __init__(self, exc_type, match):
        self.exc_type, self.match = exc_type, match

    def __enter__(self):
        return self

    def __exit__(self, typ, exc, tb):
        if typ is None:
            raise AssertionError(f"expected {self.exc_type.__name__}: {self.match}")
        return issubclass(typ, self.exc_type) and bool(re.search(self.match, str(exc)))


def run(module_globals):
    failed = 0
    for name, fn in list(module_globals.items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print("PASS", name)
            except Exception as exc:  # noqa: BLE001
                failed += 1
                print("FAIL", name, "-", type(exc).__name__, exc)
    if failed:
        raise SystemExit(f"{failed} failed")


__all__ = ["FLOORS", "floors_digest", "World", "make_law", "raises", "run", "T0", "MIN", "H", "DAY", "MAX_AHEAD_MS", "Refused", "digest",
           "identity", "copy", "Kernel", "Journal", "Accountability", "public", "keyid"]
