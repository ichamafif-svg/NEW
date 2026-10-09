"""Contract checks for full constitutional runtime integration.

These tests intentionally do not bootstrap a privileged root with a test-only
god-mode: signed genesis/quorum scenarios remain in the inherited TCB suite.
"""
import tempfile
import unittest
from pathlib import Path
from hybrid_kernel.runtime import ConstitutionalRuntime,IntegrationError
from tcb import SQLitePins

class RuntimeContract(unittest.TestCase):
    def test_pin_store_required(self):
        with self.assertRaises(IntegrationError):
            ConstitutionalRuntime(ledger_path="/tmp/nonexistent.db",pin_store=None,genesis_pin="sha256:"+"0"*64)

    def test_genesis_pin_required(self):
        with tempfile.TemporaryDirectory() as d:
            pins=SQLitePins(Path(d)/"pin.db",create=True)
            with self.assertRaises(IntegrationError):
                ConstitutionalRuntime(ledger_path=Path(d)/"journal.db",pin_store=pins,genesis_pin="not-a-pin")

    def test_same_file_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            pins=SQLitePins(Path(d)/"pin.db",create=True)
            with self.assertRaises(IntegrationError):
                ConstitutionalRuntime(ledger_path=Path(d)/"pin.db",pin_store=pins,genesis_pin="sha256:"+"0"*64)

    def test_no_unsigned_admission_method(self):
        self.assertFalse(hasattr(ConstitutionalRuntime,"judge"))
        self.assertFalse(hasattr(ConstitutionalRuntime,"allow"))
        self.assertFalse(hasattr(ConstitutionalRuntime,"commit"))

if __name__=="__main__":unittest.main()
