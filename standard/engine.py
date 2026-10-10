"""Durable operational retries for constitutional tasks, with no grant semantics.

SQLite holds scheduling metadata only. The kernel's obligation and due are the
source of truth; this store cannot close debt or attest an effect.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .service import WorkError


class WorkEngine:
    def __init__(self, path, service):
        self.service = service
        self.db = sqlite3.connect(str(Path(path)), isolation_level=None, timeout=15)
        self.db.execute("PRAGMA busy_timeout=15000")
        self.db.execute("""CREATE TABLE IF NOT EXISTS tasks (
            mode TEXT NOT NULL, id TEXT NOT NULL, obligation TEXT NOT NULL,
            due INTEGER NOT NULL, state TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0,
            next_at INTEGER NOT NULL DEFAULT 0, lease_until INTEGER NOT NULL DEFAULT 0,
            basis TEXT NOT NULL, PRIMARY KEY(mode,id))""")

    def sync(self, *, mode="RUN"):
        """Refresh routes and visible tasks; preserve retries and original due."""
        cycle = self.service.inspect(mode=mode)
        self.db.execute("BEGIN IMMEDIATE")
        try:
            for task in cycle["tasks"]:
                old = self.db.execute("SELECT due FROM tasks WHERE mode=? AND id=?",
                                      (mode, task["id"])).fetchone()
                due = min(old[0], task["due"]) if old else task["due"]
                self.db.execute("""INSERT INTO tasks(mode,id,obligation,due,state,basis)
                    VALUES(?,?,?,?,?,?) ON CONFLICT(mode,id) DO UPDATE SET
                    due=excluded.due,state=excluded.state,basis=excluded.basis""",
                    (mode, task["id"], task["obligation"], due, task["state"],
                     json.dumps(cycle["basis"], sort_keys=True)))
            # Absence from this current audit removes an operational task. Only
            # the constitutional auditor may call the obligation resolved.
            current = {t["id"] for t in cycle["tasks"]}
            for (ident,) in self.db.execute("SELECT id FROM tasks WHERE mode=?", (mode,)).fetchall():
                if ident not in current:
                    self.db.execute("DELETE FROM tasks WHERE mode=? AND id=?", (mode, ident))
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return cycle

    def claim(self, *, mode="RUN", now, lease_ms=60_000):
        """Lease one ready task to a worker; leases confer no K/T authority."""
        if type(now) is not int or now < 0 or type(lease_ms) is not int or lease_ms <= 0:
            raise WorkError("invalid scheduling horizon")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row = self.db.execute("""SELECT id,basis,attempts,due FROM tasks
                WHERE mode=? AND state='READY' AND next_at<=? AND lease_until<=?
                ORDER BY due,id LIMIT 1""", (mode, now, now)).fetchone()
            if row:
                self.db.execute("UPDATE tasks SET lease_until=?,attempts=attempts+1 WHERE mode=? AND id=?",
                                (now + lease_ms, mode, row[0]))
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        if row is None:
            return None
        return {"id": row[0], "basis": json.loads(row[1]), "attempt": row[2] + 1,
                "due": row[3], "lease_until": now + lease_ms}

    def complete_attempt(self, *, mode, task_id, lease_until, next_at):
        """Record retry timing; never mark an obligation satisfied."""
        if type(next_at) is not int or next_at < 0 or type(lease_until) is not int or lease_until <= 0:
            raise WorkError("invalid retry horizon")
        with self.db:
            changed = self.db.execute("""UPDATE tasks SET next_at=?,lease_until=0
                WHERE mode=? AND id=? AND lease_until=?""",
                (next_at, mode, task_id, lease_until)).rowcount
        if changed != 1:
            raise WorkError("stale worker lease")

    def close(self):
        self.db.close()
