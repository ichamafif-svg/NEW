"""Durable monotonic pin store for a separate rollback domain.

The operator must place this database on independently retained storage.
Two files on one restorable volume are not independent.
"""
from __future__ import annotations

import sqlite3
import os
from contextlib import closing
from pathlib import Path

from .shapes import DIGEST


class SQLitePins:
    def __init__(self, path, *, create=False):
        self.path = Path(path).resolve()
        if create:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            fd = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            os.close(fd)
            with closing(self._connect()) as db:
                db.execute("CREATE TABLE pins (size INTEGER PRIMARY KEY, head TEXT NOT NULL)")
                db.execute("CREATE TABLE domain (genesis TEXT NOT NULL)")
                db.execute("CREATE TABLE halt (reason TEXT NOT NULL)")
                db.execute("CREATE TABLE tail (size INTEGER PRIMARY KEY, raw BLOB NOT NULL)")
            directory = os.open(self.path.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        elif not self.path.is_file():
            raise FileNotFoundError("a retained pin store must never be silently recreated")

    def _connect(self):
        db = sqlite3.connect(self.path.as_uri() + "?mode=rw", uri=True, timeout=30, isolation_level=None)
        db.execute("PRAGMA synchronous=FULL")
        return db

    def bind(self, genesis):
        if not isinstance(genesis, str) or not DIGEST.fullmatch(genesis):
            raise ValueError("invalid genesis pin")
        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                row = db.execute("SELECT genesis FROM domain").fetchone()
                if row and row[0] != genesis:
                    raise ValueError("pin store belongs to another ledger")
                if not row:
                    db.execute("INSERT INTO domain VALUES (?)", (genesis,))
                db.commit()
            except BaseException:
                db.rollback()
                raise

    def halt(self, reason: str) -> None:
        """Record that two independent mechanisms disagreed. Only a human operator clears it, outside the system."""
        with closing(self._connect()) as db:
            db.execute("INSERT INTO halt (reason) VALUES (?)", (str(reason)[:500],))

    def halted(self) -> str | None:
        with closing(self._connect()) as db:
            row = db.execute("SELECT reason FROM halt LIMIT 1").fetchone()
        return row[0] if row else None

    def genesis(self) -> str | None:
        with closing(self._connect()) as db:
            row = db.execute("SELECT genesis FROM domain").fetchone()
        return row[0] if row else None

    def load(self):
        with closing(self._connect()) as db:
            row = db.execute("SELECT size, head FROM pins ORDER BY size DESC LIMIT 1").fetchone()
        return [{"size": row[0], "head": row[1]}] if row else []

    def tail(self):
        """The exact signed entry behind the highest pin, kept with it: a crash between pin and commit is repairable."""
        with closing(self._connect()) as db:
            row = db.execute("SELECT size, raw FROM tail ORDER BY size DESC LIMIT 1").fetchone()
        return (row[0], bytes(row[1])) if row else None

    def keep(self, size: int, raw: bytes) -> None:
        """Keep the exact entry about to be pinned at `size`, before the pin itself (one row: the last only)."""
        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("DELETE FROM tail")
            db.execute("INSERT INTO tail (size, raw) VALUES (?, ?)", (size, raw))
            db.commit()

    def retain(self, pin):
        if (not isinstance(pin, dict) or set(pin) != {"size", "head"} or type(pin["size"]) is not int
                or pin["size"] < 1 or not isinstance(pin["head"], str) or not DIGEST.fullmatch(pin["head"])):
            raise ValueError("invalid checkpoint")
        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                row = db.execute("SELECT size, head FROM pins ORDER BY size DESC LIMIT 1").fetchone()
                if row and (pin["size"] < row[0] or (pin["size"] == row[0] and pin["head"] != row[1])):
                    raise ValueError("checkpoint regression or fork")
                if not row or pin["size"] > row[0]:
                    db.execute("INSERT INTO pins (size, head) VALUES (?, ?)", (pin["size"], pin["head"]))
                db.commit()
            except BaseException:
                db.rollback()
                raise
