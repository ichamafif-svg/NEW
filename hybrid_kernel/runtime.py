"""Production-path integration for the inherited constitutional kernel.

Unlike the exploratory hybrid core, this facade DOES NOT accept allowed=True.
Signed entries are judged by the existing full admission kernel, checked by the
second verifier and journaled with separately retained pins. The deployment
must independently establish physical pin/egress/key custody separation.
"""
from __future__ import annotations
from pathlib import Path
from tcb import Kernel, Journal, Accountability, SQLitePins, Guard, EffectPort
from tcb.release import code_digest
from tcb.kernel import Refused
from tcb.ledger import entry
from tcb.canon import digest

class IntegrationError(ValueError):
    pass

class ConstitutionalRuntime:
    """Single constitutional admission path, never a parallel authority engine."""

    def __init__(self, *, ledger_path, pin_store, genesis_pin):
        if not isinstance(pin_store,SQLitePins):
            raise IntegrationError("An independently retained pin store is mandatory")
        if not isinstance(genesis_pin,str) or not genesis_pin.startswith("sha256:"):
            raise IntegrationError("An externally supplied genesis digest is mandatory")
        lp=Path(ledger_path).resolve()
        if lp==pin_store.path:
            raise IntegrationError("Journal and pins must be on distinct paths")
        pin_store.bind(genesis_pin)
        self.kernel=Kernel(code_pin=code_digest())
        self.accountability=Accountability(self.kernel)
        self.journal=Journal(lp,self.kernel,genesis_pin=genesis_pin,
                             checkpoints=pin_store,accountability=self.accountability)

    def admit(self,envelope):
        """Add one independently signed canonical envelope, no caller-controlled allow flag."""
        if not isinstance(envelope,dict):
            raise IntegrationError("A signed envelope is mandatory")
        def build(s):
            return entry(s["size"],s["head"],envelope)
        return self.journal.transact(build)

    def snapshot(self):
        return self.journal.snapshot()

    def health(self,*,required_at=None):
        return self.journal.health(required_at=required_at)

    def guard(self,*,identity,signer,operation_handlers):
        """Privileged adapter only; handler must be physically exclusive."""
        return Guard(self.journal,identity,signer,EffectPort(operation_handlers))

    def close(self):
        self.journal.close()
    def __enter__(self):return self
    def __exit__(self,*_):self.close()
