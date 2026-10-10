"""Compatibility name for the single anchored constitutional admission store.

There is no unanchored checkpoint database or alternate receipt interpreter.
Genesis itself is a signed constitutional entry with a human quorum and an
externally selected pin. Recovery restores the exact independently pinned tail.
"""
from .runtime import ConstitutionalRuntime, IntegrationError

StoreError = IntegrationError


class SQLiteAdmission(ConstitutionalRuntime):
    """Same admission, checker, append-only journal and pins as the runtime."""

    def read(self):
        return self.snapshot()

    def recover_tail(self, candidate=None):
        return self.journal.recover_tail(candidate)
