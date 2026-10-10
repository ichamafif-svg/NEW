"""Anchored integration of the single hybrid constitutional interpreter.

Only signed statements enter this boundary. Journal commits after the independent
consequence check and retains the exact prefix before acknowledgment. Physical
pin restoration domains, key custody and egress exclusivity remain T contracts.
"""
from __future__ import annotations
from pathlib import Path
from tcb import Journal, Auditor, SQLitePins, Guard, EffectPort
from .core import Kernel
from tcb.release import code_digest
from .core import Refused
from tcb.ledger import entry
from tcb.shapes import DIGEST

class IntegrationError(ValueError):
    pass

class ConstitutionalRuntime:
    """Single constitutional admission path, never a parallel authority engine."""

    def __init__(self, *, ledger_path, pin_store, genesis_pin):
        if not isinstance(pin_store,SQLitePins):
            raise IntegrationError("An independently retained pin store is mandatory")
        if not isinstance(genesis_pin,str) or not DIGEST.fullmatch(genesis_pin):
            raise IntegrationError("An externally supplied genesis digest is mandatory")
        lp=Path(ledger_path).resolve()
        if lp==pin_store.path:
            raise IntegrationError("Journal and pins must be on distinct paths")
        pin_store.bind(genesis_pin)
        self.kernel=Kernel(code_pin=code_digest())
        self.accountability=Auditor()
        self.journal=Journal(lp,self.kernel,genesis_pin=genesis_pin,
                             checkpoints=pin_store,accountability=self.accountability)

    def admit(self,envelope,*,validity_check=None):
        """Add one independently signed canonical envelope, no caller-controlled allow flag."""
        if not isinstance(envelope,dict):
            raise IntegrationError("A signed envelope is mandatory")
        def build(s):
            if validity_check is not None:
                validity_check()
            return entry(s["size"],s["head"],envelope)
        return self.journal.transact(build)

    def snapshot(self):
        return self.journal.snapshot()

    def health(self,*,required_at=None):
        return self.journal.health(required_at=required_at)

    def guard(self,*,identity,signer,operation_handlers,validity_check=None):
        """Privileged adapter only; handler must be physically exclusive."""
        return Guard(self.journal,identity,signer,EffectPort(operation_handlers),
                     validity_check=validity_check)

    def close(self):
        self.journal.close()
    def __enter__(self):return self
    def __exit__(self,*_):self.close()
