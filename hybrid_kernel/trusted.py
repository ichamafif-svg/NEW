"""Signed boundary to the sole constitutional interpreter.

A trusted source authenticates statements; it cannot sign an `allowed` receipt
and replace constitutional authority. The ledger domain, exact prefix, pinned
law, principal quorum and proof eligibility are all derived by Kernel.
"""
from __future__ import annotations

from .core import Kernel, Refused
from tcb.ledger import entry


def judge_signed(kernel, state, envelope):
    """Pure admission preview, never a bearer authorization or durable commit."""
    if not isinstance(kernel, Kernel):
        raise Refused("TRUST.KERNEL", "the pinned constitutional interpreter is required")
    if not isinstance(envelope, dict):
        raise Refused("SIG.ENVELOPE", "a canonical signed statement is required")
    return kernel.judgment(state, entry(state["size"], state["head"], envelope))
