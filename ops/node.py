"""One participant's view of a Standard journal: open it, sign as one identity, append.

Outside the TCB: every entry written here is judged again by the kernel and the second judge. A node holds only the
private keys of the identities it acts as; keys never live in a repository (they come from a directory or from the
environment, one JSON map {name: base64 raw Ed25519 private key})."""
from __future__ import annotations

import base64
import json
import os
import time
import uuid
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat, PublicFormat

from tcb import Journal, Kernel, SQLitePins, entry
from tcb.crypto import keyid
from tcb.floor0 import MAX_AHEAD_MS
from tcb.sign import envelope

KINDS = {"icham": "human", "second": "human", "third": "human", "fourth": "human", "agent": "agent", "scanner": "oracle", "guard": "guard",
         "w1": "witness", "w2": "witness", "sentinel": "sentinel"}
HUMANS = ("icham", "second")


def public(key) -> str:
    return base64.b64encode(key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)).decode()


def new_keys(names) -> dict:
    return {n: base64.b64encode(Ed25519PrivateKey.generate().private_bytes(
        Encoding.Raw, PrivateFormat.Raw, NoEncryption())).decode() for n in names}


def load_keys(source: str | None = None) -> dict:
    """From a JSON file path, or from STANDARD_KEYS (JSON text). Unknown names are refused."""
    text = Path(source).read_text() if source else os.environ.get("STANDARD_KEYS", "{}")
    raw = json.loads(text)
    if set(raw) - set(KINDS):
        raise ValueError(f"unknown identities in key material: {sorted(set(raw) - set(KINDS))}")
    return {n: Ed25519PrivateKey.from_private_bytes(base64.b64decode(v)) for n, v in raw.items()}


def root_of(publics: dict) -> dict:
    """The root names every identity by its public key only."""
    return {"threshold": 2, "identities": {
        n: {"kind": KINDS[n], "keys": [{"alg": "ed25519", "public": p, "keyid": keyid(p)}]} for n, p in publics.items()}}


class Node:
    def __init__(self, state_dir, keys: dict, *, create=False, expected_genesis=None):
        """`expected_genesis` comes from outside the state (an admin-only setting): a journal carried on a branch
        anyone with write access could replace is accepted only if it is the genesis the humans chose."""
        self.dir = Path(state_dir)
        self.keys = keys
        self.kernel = Kernel()
        meta = self.dir / "genesis.json"
        self.genesis = json.loads(meta.read_text())["pin"] if meta.exists() else None
        if not create and (expected_genesis is None or self.genesis != expected_genesis):
            raise ValueError("the state is not the externally pinned genesis")
        self.pins = SQLitePins(self.dir / "pins" / "pins.sqlite3", create=create)
        from tcb import Auditor
        self.journal = Journal(self.dir / "journal" / "journal.sqlite3", self.kernel, genesis_pin=self.genesis,
                               checkpoints=self.pins, accountability=Auditor())
        if self.genesis:
            self.pins.bind(self.genesis)

    @property
    def state(self):
        return self.journal.snapshot()

    def now(self) -> int:
        """Witnessed time: never behind the journal, never further ahead of the last checkpoint than FLOOR-0 allows."""
        s = self.state
        real = int(time.time() * 1000)
        ceiling = (s["anchor_at"] + MAX_AHEAD_MS - 1) if s.get("anchor_at") else real
        return max(s["last_at"] + 1, min(real, ceiling))

    def signer(self, name):
        key = self.keys[name]
        return keyid(public(key)), key

    def build(self, kind, author, signers=(), at=None, **fields):
        def make(s):
            body = {"id": f"{kind}-{uuid.uuid4().hex[:16]}", "at": at or self.now(), "author": author, **fields}
            env = envelope("genesis" if kind == "genesis" else s["domain"], kind, body,
                           [self.signer(x) for x in (signers or (author,))])
            return entry(s["size"], s["head"], env)
        return make

    def add(self, kind, author, signers=(), at=None, **fields) -> dict:
        admitted = self.journal.transact(self.build(kind, author, signers, at, **fields))[0]
        return admitted

    def retain(self):
        s = self.state
        self.pins.retain({"size": s["size"], "head": s["head"]})

    def checkpoint(self):
        """Both witnesses sign the current head at real time: the only way the journal's clock moves forward."""
        s = self.state
        at = max(s["last_at"] + 1, int(time.time() * 1000))
        return self.add("checkpoint", "w1", ("w1", "w2"), at=at, size=s["size"], head=s["head"])

    def close(self):
        self.journal.close()
