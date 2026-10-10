"""T09 escalation delivery outbox: persist before send, confirm by signed readback.

The transport must honor the idempotency key and independently attest delivery.
The database, provider keys, credentials and actual recipient mapping require
operator-controlled trust domains; this module does not certify them.
"""
from __future__ import annotations

import base64
import os
import sqlite3
from contextlib import closing
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from tcb.canon import canon, digest, parse

PREFIX = b"standard:delivery-receipt:v1\x00"


class DeliveryError(ValueError):
    pass


class EscalationOutbox:
    """An unknown departure is read back, never resent on timeout alone."""

    def __init__(self, path, *, transport, provider_keys, health_reader, genesis,
                 validity_check, create=False):
        if not callable(getattr(transport, "send", None)) or not callable(getattr(transport, "readback", None)):
            raise DeliveryError("DELIVERY.TRANSPORT")
        if not isinstance(provider_keys, dict) or not provider_keys or any(
            not isinstance(k, str) or not isinstance(v, bytes) or len(v) != 32
            for k, v in provider_keys.items()
        ):
            raise DeliveryError("DELIVERY.PROVIDER_KEYS")
        if not callable(health_reader) or not callable(validity_check):
            raise DeliveryError("DELIVERY.BOUNDARY")
        self.path, self.transport, self.provider_keys = Path(path).resolve(), transport, dict(provider_keys)
        self.health_reader, self.genesis, self.validity_check = health_reader, genesis, validity_check
        if create:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            fd = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            os.close(fd)
            with closing(self._db()) as db:
                db.execute("CREATE TABLE deliveries (key TEXT PRIMARY KEY, payload BLOB NOT NULL, "
                           "status TEXT NOT NULL, receipt BLOB)")
            directory = os.open(self.path.parent, os.O_RDONLY | os.O_DIRECTORY)
            try: os.fsync(directory)
            finally: os.close(directory)
        elif not self.path.is_file():
            raise DeliveryError("DELIVERY.OUTBOX_MISSING")

    def _db(self):
        db = sqlite3.connect(self.path.as_uri() + "?mode=rw", uri=True, isolation_level=None, timeout=10)
        db.execute("PRAGMA synchronous=FULL")
        return db

    def enqueue(self):
        """Only a named, current, authenticated health prefix creates deliveries."""
        self.validity_check()
        verdict = self.health_reader()
        if (not isinstance(verdict, dict) or verdict.get("state") not in
                ("PROVEN", "IN_PROGRESS", "ESCALATED") or verdict.get("current") is False
                or type(verdict.get("size")) is not int or verdict["size"] < 1
                or not isinstance(verdict.get("head"), str)
                or not isinstance(verdict.get("escalated"), list)):
            raise DeliveryError("DELIVERY.UNTRUSTED_HEALTH")
        if verdict["state"] != "ESCALATED" and verdict["escalated"]:
            raise DeliveryError("DELIVERY.INCONSISTENT_HEALTH")
        staged = []
        for gap in verdict["escalated"]:
            if not isinstance(gap, dict): raise DeliveryError("DELIVERY.GAP")
            recipients = gap.get("escalated_to")
            if (not isinstance(recipients, list) or not recipients or
                    any(not isinstance(r, str) or not r for r in recipients) or
                    type(gap.get("opened")) is not int or type(gap.get("due")) is not int or
                    not isinstance(gap.get("obligation"), str)):
                raise DeliveryError("DELIVERY.GAP")
            key = digest({"genesis": self.genesis, "obligation": gap["obligation"],
                          "opened": gap["opened"], "recipients": recipients})
            payload = {"key": key, "genesis": self.genesis, "head": verdict["head"],
                       "size": verdict["size"], "obligation": gap["obligation"],
                       "opened": gap["opened"], "due": gap["due"], "recipients": recipients}
            raw = canon(payload)
            if len(raw) > 8192: raise DeliveryError("DELIVERY.SIZE")
            staged.append((key, raw))
        with closing(self._db()) as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                for key, raw in staged:
                    db.execute("INSERT OR IGNORE INTO deliveries VALUES (?, ?, 'pending', NULL)",
                               (key, raw))
                db.commit()
            except BaseException:
                db.rollback()
                raise
        return [key for key, _ in staged]

    def deliver(self, key):
        """Persist attempt before the network call. A later call only reads back."""
        with closing(self._db()) as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                row = db.execute("SELECT payload, status FROM deliveries WHERE key=?", (key,)).fetchone()
                if row is None: raise DeliveryError("DELIVERY.UNKNOWN_KEY")
                raw, status = row
                if status == "delivered":
                    db.commit()
                    return status
                if status == "pending":
                    db.execute("UPDATE deliveries SET status='attempted' WHERE key=?", (key,))
                db.commit()
            except BaseException:
                db.rollback()
                raise
        if status == "pending":
            self.validity_check()
            try: self.transport.send(key, parse(raw))
            except Exception: pass  # An exception may follow a successful send.
        try: receipt = self.transport.readback(key)
        except Exception: return "UNKNOWN"
        if not self._valid_receipt(receipt, raw, key): return "UNKNOWN"
        with closing(self._db()) as db:
            db.execute("UPDATE deliveries SET status='delivered', receipt=? WHERE key=?",
                       (canon(receipt), key))
        return "delivered"

    def _valid_receipt(self, receipt, raw, key):
        try:
            if not isinstance(receipt, dict) or set(receipt) != {"claim", "signature"}:
                return False
            claim = receipt["claim"]
            if not isinstance(claim, dict) or set(claim) != {
                "key", "payload_digest", "recipients_digest", "provider", "delivered_at"
            } or claim["key"] != key or claim["payload_digest"] != digest(parse(raw)):
                return False
            payload = parse(raw)
            if (claim["recipients_digest"] != digest(payload["recipients"])
                    or type(claim["delivered_at"]) is not int or claim["delivered_at"] < payload["due"]):
                return False
            key_bytes = self.provider_keys.get(claim["provider"])
            if key_bytes is None: return False
            if not isinstance(receipt["signature"], str) or len(receipt["signature"]) > 128:
                return False
            signature = base64.b64decode(receipt["signature"], validate=True)
            if len(signature) != 64: return False
            Ed25519PublicKey.from_public_bytes(key_bytes).verify(signature, PREFIX + canon(claim))
            return True
        except (InvalidSignature, ValueError, TypeError, KeyError, AttributeError):
            return False

    def status(self, key):
        with closing(self._db()) as db:
            row = db.execute("SELECT status, receipt FROM deliveries WHERE key=?", (key,)).fetchone()
        if row is None: raise DeliveryError("DELIVERY.UNKNOWN_KEY")
        return {"state": row[0], "receipt": parse(row[1]) if row[1] is not None else None}
