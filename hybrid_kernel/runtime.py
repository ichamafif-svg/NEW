"""Anchored integration of the single hybrid constitutional interpreter.

Only signed statements enter this boundary. Journal commits after the independent
consequence check and retains the exact prefix before acknowledgment. Physical
pin restoration domains, key custody and egress exclusivity remain T contracts.
"""
from __future__ import annotations
from pathlib import Path
from tcb import Journal, Auditor, Guard, EffectPort
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
        if pin_store is None or any(not callable(getattr(pin_store, name, None))
                                    for name in ("bind", "load", "retain", "keep", "tail", "halt", "halted")):
            raise IntegrationError("A durable pin port with exact-tail recovery is mandatory")
        if not isinstance(genesis_pin,str) or not DIGEST.fullmatch(genesis_pin):
            raise IntegrationError("An externally supplied genesis digest is mandatory")
        lp=Path(ledger_path).resolve()
        if hasattr(pin_store,"path") and lp==Path(pin_store.path).resolve():
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

    def guard(self,*,identity,signer,operation_handlers=None,effect_port=None,validity_check=None):
        """Local adapters are possible; governed deployments pin their port at installation."""
        if (operation_handlers is None) == (effect_port is None):
            raise IntegrationError("exactly one explicit effect port is required")
        port = EffectPort(operation_handlers) if effect_port is None else effect_port
        return Guard(self.journal,identity,signer,port,
                     validity_check=validity_check)

    def close(self):
        self.journal.close()
    def __enter__(self):return self
    def __exit__(self,*_):self.close()
