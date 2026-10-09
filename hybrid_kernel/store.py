"""Single-process/SQLite transactional admission boundary.

Not a full TCB: database rollback outside this process remains possible without
an independent monotonic checkpoint. No physical effects are dispatched.
"""
from __future__ import annotations
import sqlite3
from pathlib import Path
from tcb.canon import canon,parse,digest
from .core import genesis,commit,Invalid
from .trusted import judge_signed

class StoreError(ValueError):pass

class SQLiteAdmission:
    def __init__(self,path,constitution,trust_root):
        self.path=str(Path(path))
        self.constitution=constitution
        self.trust_root=trust_root
        self.db=sqlite3.connect(self.path,timeout=5.0,isolation_level=None)
        self.db.execute("PRAGMA busy_timeout=5000")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("CREATE TABLE IF NOT EXISTS checkpoint (slot INTEGER PRIMARY KEY CHECK(slot=1), state BLOB NOT NULL)")
        self.db.execute("CREATE TABLE IF NOT EXISTS admission (seq INTEGER PRIMARY KEY, request_id TEXT NOT NULL UNIQUE, previous TEXT NOT NULL, state_digest TEXT NOT NULL, verdict BLOB NOT NULL, envelope_digest TEXT NOT NULL)")
    def close(self):self.db.close()
    def __enter__(self):return self
    def __exit__(self,*_):self.close()
    def initialize(self):
        """Explicit one-time genesis; never overwrites an existing database."""
        self.db.execute("BEGIN IMMEDIATE")
        try:
            present=self.db.execute("SELECT 1 FROM checkpoint WHERE slot=1").fetchone()
            if present:raise StoreError("GENESIS.EXISTS")
            if self.db.execute("SELECT 1 FROM admission LIMIT 1").fetchone():
                raise StoreError("GENESIS.LEDGER_EXISTS")
            self.db.execute("INSERT INTO checkpoint(slot,state) VALUES(1,?)",(canon(genesis(self.constitution)),))
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise
    def read(self):
        row=self.db.execute("SELECT state FROM checkpoint WHERE slot=1").fetchone()
        if row is None:raise StoreError("GENESIS.MISSING")
        state=parse(row[0])
        if state["law"]!=self.constitution["pinned"]:raise StoreError("LAW.PIN")
        n=self.db.execute("SELECT COUNT(*), MAX(state_digest) FROM admission").fetchone()
        if n[0]!=state["epoch"]:raise StoreError("LEDGER.COUNT")
        if n[0]:
            last=self.db.execute("SELECT state_digest FROM admission ORDER BY seq DESC LIMIT 1").fetchone()[0]
            if last!=digest(state):raise StoreError("LEDGER.HEAD")
        return state
    def admit(self,request,envelope):
        """Serializes fresh signed admission, judgment and durable state update.

        Does NOT cause an effect. Returned authorization is NOT an executable
        bearer token: a fenced dispatcher with external egress exclusivity is required.
        """
        self.db.execute("BEGIN IMMEDIATE")
        try:
            state=self.read()
            if self.db.execute("SELECT 1 FROM admission WHERE request_id=?",(request["id"],)).fetchone():
                raise StoreError("ADMISSION.REPLAY")
            # Judge every time inside the current exclusive transaction. Never
            # accept a Decision supplied by the caller.
            verdict=judge_signed(state,self.constitution,request,envelope,self.trust_root)
            if verdict.verdict!="ACCEPT":
                self.db.execute("ROLLBACK")
                return verdict
            next_state=commit(state,verdict)
            self.db.execute("INSERT INTO admission(seq,request_id,previous,state_digest,verdict,envelope_digest) VALUES (?,?,?,?,?,?)",
              (next_state["epoch"],request["id"],digest(state),digest(next_state),canon(verdict.wire()),digest(envelope)))
            updated=self.db.execute("UPDATE checkpoint SET state=? WHERE slot=1",(canon(next_state),))
            if updated.rowcount!=1:raise StoreError("COMMIT.NO_STATE")
            self.db.execute("COMMIT")
            return verdict
        except BaseException:
            if self.db.in_transaction:self.db.execute("ROLLBACK")
            raise
