"""Single anchored store: signed genesis, replay, rollback and exact recovery."""
import copy
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixture import World, T0, Refused, digest, public, keyid
from tcb.sign import envelope
from tcb.canon import parse
from hybrid_kernel.core import Kernel
from hybrid_kernel.store import SQLiteAdmission, StoreError


class StoreTests(unittest.TestCase):
    def test_signed_genesis_once_and_reopen(self):
        with tempfile.TemporaryDirectory() as d:
            w = World(tmp=d, genesis=False)
            candidate, _ = w.signed("genesis", "alice", T0, ["alice", "bob"], root=w.root, law=w.law)
            from tcb.crypto import open_envelope
            _, body, _, _ = open_envelope(candidate["envelope"])
            pin = digest(body)
            with SQLiteAdmission(ledger_path=w.path, pin_store=w.pins, genesis_pin=pin) as store:
                store.admit(candidate["envelope"])
                self.assertEqual(store.read()["size"], 1)
                with self.assertRaises(Refused):
                    store.admit(candidate["envelope"])
            with SQLiteAdmission(ledger_path=w.path, pin_store=w.pins, genesis_pin=pin) as store:
                self.assertEqual(store.read()["domain"], pin)
                self.assertEqual(store.health()["state"], "IN_PROGRESS")

    def test_missing_independent_pin_refused(self):
        with self.assertRaises(StoreError):
            SQLiteAdmission(ledger_path="none", pin_store=None, genesis_pin=digest("genesis"))

    def test_rollback_against_retained_pin_detected(self):
        w = World()
        w.add("freeze", "carol", T0 + 1, scope="*")
        with sqlite3.connect(w.path) as db:
            db.execute("DELETE FROM entries WHERE seq=1")
        with self.assertRaises(ValueError):
            w.journal.snapshot()

    def test_recovery_restores_only_exact_pinned_tail(self):
        w = World()
        candidate, ident = w.signed("freeze", "carol", T0 + 1, scope="*")
        from tcb.canon import canon, raw_digest
        w.pins.keep(2, canon(candidate))
        w.pins.retain({"size": 2, "head": raw_digest(canon(candidate))})
        with self.assertRaises(ValueError):
            w.journal.snapshot()
        recovered = w.journal.recover_tail()
        self.assertEqual(recovered["size"], 2)
        self.assertEqual(recovered["frozen"]["*"], ident)


if __name__ == "__main__":
    unittest.main()
