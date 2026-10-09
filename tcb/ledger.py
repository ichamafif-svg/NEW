"""HIST outside the kernel's step: the entry form, rollback detection against externally retained checkpoints (F0-10),
and the durable local journal.

The journal keeps the verified kernel state in memory and only absorbs rows it has not seen, so a write costs one
decision, not a replay. A row is trusted only after the kernel re-judges it. If the tip the cache verified is gone or
changed, the cache is dropped and the whole journal is replayed (and retained checkpoints then detect the rollback)."""
from __future__ import annotations

import sqlite3
import threading
import time
from collections.abc import Mapping
from contextlib import closing, contextmanager
from pathlib import Path

from .canon import canon, parse, raw_digest
from .invariants import Disagreement, Invariants
from .kernel import Refused, apply, empty
from .release import code_digest
from .shapes import DIGEST


def _view(value):
    """Lazy read-only interface for callers outside the state reducer."""
    if isinstance(value, dict):
        return _ReadOnly(value)
    if isinstance(value, (list, tuple)):
        return tuple(_view(item) for item in value)
    if isinstance(value, set):
        return frozenset(value)
    return value


class _ReadOnly(Mapping):
    def __init__(self, data):
        self._data = data

    def __getitem__(self, key):
        return _view(self._data[key])

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def __deepcopy__(self, memo):
        import copy
        return copy.deepcopy(self._data, memo)


def entry(seq: int, prev: str | None, envelope: dict) -> dict:
    return {"seq": seq, "prev": prev, "envelope": envelope}


def rollback_problems(heads: list[str], checkpoints) -> list[str]:
    """heads[i] is the head after entry i. checkpoints: {size, head} as retained outside the journal."""
    problems = []
    for c in checkpoints:
        if not isinstance(c, dict) or set(c) != {"size", "head"}:
            problems.append("malformed retained checkpoint")
            continue
        size, head = c["size"], c["head"]
        if type(size) is not int or size < 1 or not isinstance(head, str) or not DIGEST.fullmatch(head):
            problems.append("invalid retained checkpoint size or head")
        elif size > len(heads):
            problems.append(f"checkpoint at {size} is beyond the journal ({len(heads)}): truncated")
        elif heads[size - 1] != head:
            problems.append(f"entry {size} differs from its checkpoint: rewritten")
    return problems


def audit(kernel, accountability, entries, *, genesis_pin: str, checkpoints, required_at=None) -> dict:
    """What an external auditor runs: replay from nothing, check the pins, derive the verdict."""
    if not isinstance(genesis_pin, str) or not checkpoints:
        raise Refused("HIST.PIN", "external genesis and retained checkpoints are required")
    ks, acc, heads, invariants = empty(), accountability.empty(), [], Invariants()
    for e in entries:
        record, delta = kernel.decide(ks, e)
        try:
            invariants.check(ks, record, delta, e, kernel.law_by_digest(record["law"]))
        except Disagreement as exc:
            raise Refused("HALT.DISAGREEMENT", str(exc)) from None
        apply(ks, delta)
        heads.append(ks["head"])
        accountability.feed(acc, _view(ks), _view(record))
    if ks["domain"] != genesis_pin:
        raise Refused("HIST.GENESIS_PIN", "the journal is not the externally pinned genesis")
    problems = rollback_problems(heads, checkpoints)
    if problems:
        raise Refused("HIST.ROLLBACK", "; ".join(problems))
    return accountability.health(acc, ks, required_at=required_at)


class Journal:
    """Local, durable journal. All writers and guards must use this same SQLite database.

    BEGIN IMMEDIATE orders admission, pin-before-commit and dispatch. Every write is durably pinned before acknowledgment. The database
    file, the host and the externally retained pins are trusted; this is not a distributed consensus service."""

    def __init__(self, path, kernel, genesis_pin=None, checkpoints=(), accountability=None):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.kernel, self.auditor = kernel, accountability          # layer 3, injected: never imported here
        self.genesis_pin = genesis_pin
        self.pin_store = checkpoints if callable(getattr(checkpoints, "load", None)) else None
        self.checkpoints = None if self.pin_store is not None else tuple(dict(c) for c in checkpoints)
        if kernel.code_pin != code_digest():
            raise ValueError("code release differs from the kernel pin")
        if (self.pin_store is not None and hasattr(self.pin_store, "path")
                and self.pin_store.path.resolve() == self.path.resolve()):
            raise ValueError("pins must be retained independently from the journal")
        self._lock = threading.RLock()
        self.invariants = Invariants()
        self.halted = None
        self._reset()
        with closing(self._connect()) as db:
            db.execute("CREATE TABLE IF NOT EXISTS entries (seq INTEGER PRIMARY KEY, raw BLOB NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS reservations (token TEXT PRIMARY KEY, seq INTEGER NOT NULL)")

    def _connect(self):
        db = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        db.execute("PRAGMA synchronous=FULL")
        return db

    def _reset(self):
        self.state, self.heads = empty(), []

    def _halt(self, reason):
        self.halted = reason
        if self.pin_store is not None:
            self.pin_store.halt(reason)
        raise Refused("HALT.DISAGREEMENT", reason)

    def _judge(self, candidate):
        record, delta = self.kernel.decide(self.state, candidate)
        try:
            self.invariants.check(self.state, record, delta, candidate, self.kernel.law_by_digest(record["law"]))
        except Disagreement as exc:
            self._halt(str(exc))
        except Exception as exc:
            self._halt("independent check failed: " + type(exc).__name__)
        return record, delta

    def _absorb(self, seq, raw):
        if seq != len(self.heads):
            raise ValueError("the journal has a gap")
        e = parse(raw)
        try:
            record, delta = self._judge(e)
        except Refused as r:
            raise ValueError(f"stored entry {seq} is refused by this kernel: {r}") from None
        apply(self.state, delta)
        self.heads.append(self.state["head"])

    def _sync(self, db, *, check_pins=True):
        reason = self.halted or (self.pin_store.halted() if self.pin_store is not None else None)
        if reason:
            raise Refused("HALT.DISAGREEMENT", reason)
        n = len(self.heads)
        rows = db.execute("SELECT seq, raw FROM entries WHERE seq >= ? ORDER BY seq", (max(n - 1, 0),)).fetchall()
        if n:
            if not rows or rows[0][0] != n - 1 or raw_digest(rows[0][1]) != self.heads[-1]:
                self._reset()
                rows = db.execute("SELECT seq, raw FROM entries ORDER BY seq").fetchall()
            else:
                rows = rows[1:]
        for seq, raw in rows:
            self._absorb(seq, raw)
        retained = self.pin_store.load() if self.pin_store is not None else self.checkpoints
        problems = rollback_problems(self.heads, retained) if check_pins else []
        if problems:
            raise ValueError("retained checkpoint mismatch: " + "; ".join(problems))
        if self.heads and self.genesis_pin is not None and self.state["domain"] != self.genesis_pin:
            raise ValueError("genesis differs from the external pin")
        if check_pins and self.pin_store is not None and self.heads:
            if retained != [{"size": self.state["size"], "head": self.state["head"]}]:
                raise ValueError("unretained journal tail: recovery is required")

    def snapshot(self):
        """A lazy read-only view of the verified state (live across later writes)."""
        with self._lock, closing(self._connect()) as db:
            db.execute("BEGIN")
            try:
                self._sync(db)
            finally:
                db.rollback()
        return _view(self.state)

    def transact(self, builder):
        """Build, judge and append one signed entry while holding the write lock."""
        with self._lock, closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                self._sync(db)
                if self.pin_store is None:
                    raise Refused("HIST.PIN", "every write requires a live durable pin store")
                candidate = builder(_view(self.state))
                record, delta = self._judge(candidate)
                raw = canon(candidate)
                parse(raw)                 # signed entries keep the separate 1 MiB limit
                db.execute("INSERT INTO entries (seq, raw) VALUES (?, ?)", (self.state["size"], raw))
                if record["kind"] == "reservation":
                    try:
                        db.execute("INSERT INTO reservations VALUES (?, ?)",
                                   (record["body"]["token"], self.state["size"]))
                    except sqlite3.IntegrityError:
                        self._halt("a token was reserved twice")
                domain = self.state["domain"] or next(op[2] for op in delta if op[:2] == ("set", "domain"))
                if self.genesis_pin is not None and domain != self.genesis_pin:
                    raise Refused("HIST.GENESIS_PIN", "entry differs from the external genesis pin")
                self.pin_store.bind(domain)
                # Pin FIRST, while SQLite still excludes every other writer.
                # A crash before journal commit leaves a detectable pin ahead, never forgotten authority.
                if hasattr(self.pin_store, "keep"):
                    self.pin_store.keep(self.state["size"] + 1, raw)     # the entry first, so a pin always has its tail
                self.pin_store.retain({"size": self.state["size"] + 1, "head": raw_digest(raw)})
                if self.pin_store.load() != [{"size": self.state["size"] + 1, "head": raw_digest(raw)}]:
                    raise ValueError("new entry pin was not retained")
                db.commit()
            except BaseException:
                db.rollback()
                raise
            apply(self.state, delta)
            self.heads.append(self.state["head"])
            return candidate, _view(self.state)

    def append(self, candidate):
        return self.transact(lambda _state: candidate)[1]

    @contextmanager
    def effect_gate(self):
        """No local writer can acknowledge a restriction between rejudging and dispatch."""
        with self._lock, closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                self._sync(db)
                yield _view(self.state)
            finally:
                db.rollback()

    def recover_tail(self, candidate=None):
        """Explicit repair of the exact signed last entry after pin-before-commit interruption. Without a candidate,
        the entry kept beside the pin is used: nobody needs to have held it."""
        if self.pin_store is None:
            raise Refused("HIST.PIN", "recovery needs a live retained pin")
        with self._lock, closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                self._sync(db, check_pins=False)
                kept = self.pin_store.tail() if candidate is None and hasattr(self.pin_store, "tail") else None
                if candidate is None and (kept is None or kept[0] != self.state["size"] + 1):
                    raise ValueError("no kept entry for the pinned tail")
                candidate = parse(kept[1]) if candidate is None else candidate
                raw = canon(candidate)
                parse(raw)
                expected = [{"size": self.state["size"] + 1, "head": raw_digest(raw)}]
                if self.pin_store.load() != expected:
                    raise ValueError("recovery must restore exactly the independently pinned tail")
                record, delta = self._judge(candidate)
                domain = self.state["domain"] or next(op[2] for op in delta if op[:2] == ("set", "domain"))
                if self.genesis_pin is not None and domain != self.genesis_pin:
                    raise Refused("HIST.GENESIS_PIN", "recovery differs from the external genesis pin")
                self.pin_store.bind(domain)
                db.execute("INSERT INTO entries VALUES (?, ?)", (self.state["size"], raw))
                if record["kind"] == "reservation":
                    db.execute("INSERT INTO reservations VALUES (?, ?)", (record["body"]["token"], self.state["size"]))
                db.commit()
            except BaseException:
                db.rollback()
                raise
            apply(self.state, delta)
            self.heads.append(self.state["head"])
            return _view(self.state)

    def close(self):
        if getattr(self, "auditor", None) is not None and hasattr(self.auditor, "close"):
            self.auditor.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def __del__(self):
        self.close()

    # ---- read-only interface for the accountability layer (layer 3 reads, never writes) -------------------------
    def prefix(self) -> dict:
        """The verified prefix as of now: its time, head, size, heads and the retained pins."""
        with self._lock, closing(self._connect()) as db:
            db.execute("BEGIN")
            try:
                self._sync(db)
                retained = self.pin_store.load() if self.pin_store is not None else self.checkpoints
                return {"as_of": self.state["last_at"], "head": self.state["head"], "size": self.state["size"],
                        "heads": list(self.heads), "retained": list(retained or ())}
            finally:
                db.rollback()

    def raw_rows(self, start: int, end: int, limit: int = 128) -> list:
        with closing(self._connect()) as db:
            return [raw for (raw,) in db.execute(
                "SELECT raw FROM entries WHERE seq >= ? AND seq < ? ORDER BY seq LIMIT ?", (start, end, limit))]

    def retained(self) -> list:
        return list((self.pin_store.load() if self.pin_store is not None else self.checkpoints) or ())

    def health(self, *, required_at=None, timeout=30, prefix=False):
        """Delegates to the accountability layer injected at construction; the journal itself computes nothing."""
        if self.genesis_pin is None:
            raise Refused("HIST.PIN", "an externally pinned genesis is required")
        if self.auditor is None:
            raise ValueError("this journal has no accountability layer")
        return self.auditor.health(self, required_at=required_at, timeout=timeout, prefix=prefix)
