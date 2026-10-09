"""Incremental accountability reducer. No filesystem or provider access after bootstrap."""
import struct
import sys

from .accountability import Accountability
from .canon import canon, parse
from .kernel import Kernel, empty
from .invariants import Invariants
from .ledger import _view, rollback_problems
from .sandbox import MAX_PACKET, MAX_REPLY, lock_down


def main(mode, code_pin):
    if mode != "health":
        raise ValueError("only the accountability worker is supported")
    lock_down()
    kernel, accountability, invariants = None, None, None
    ks, acc, heads = empty(), None, []
    while True:
        header = sys.stdin.buffer.read(4)
        if not header:
            return
        try:
            if len(header) != 4:
                raise ValueError("truncated frame")
            length = struct.unpack("!I", header)[0]
            if length > MAX_PACKET:
                raise ValueError("oversized frame")
            raw = sys.stdin.buffer.read(length)
            if len(raw) != length:
                raise ValueError("truncated packet")
            packet = parse(raw, max_bytes=MAX_PACKET)
            op = packet["op"]
            if op == "init" and kernel is None:
                kernel = Kernel(code_pin=code_pin)
                accountability = Accountability(kernel)
                invariants = Invariants()
                acc = accountability.empty()
                genesis_pin = packet["genesis_pin"]
                value = {"size": 0, "head": None}
            elif op == "entry" and kernel is not None:
                e = packet["entry"]
                parse(canon(e))                  # preserve the signed-entry limit
                record, delta = kernel.decide(ks, e)
                invariants.check(ks, record, delta, e, kernel.law_by_digest(record["law"]))
                from .kernel import apply
                apply(ks, delta)
                heads.append(ks["head"])
                accountability.feed(acc, _view(ks), _view(record))
                value = {"size": ks["size"], "head": ks["head"]}
            elif op == "health" and kernel is not None:
                if ks["domain"] != genesis_pin or rollback_problems(heads, packet["checkpoints"]):
                    raise ValueError("genesis or retained checkpoint mismatch")
                value = {**accountability.health(acc, ks, required_at=packet["required_at"]),
                         "head": ks["head"], "size": ks["size"]}
            else:
                raise ValueError("invalid worker operation")
            reply = canon({"ok": True, "value": value})
            if len(reply) > MAX_REPLY:
                raise ValueError("oversized reply")
        except BaseException as exc:
            reply = canon({"ok": False, "value": type(exc).__name__})
            sys.stdout.buffer.write(struct.pack("!I", len(reply)) + reply)
            sys.stdout.buffer.flush()
            return                               # never reuse a partially folded state
        sys.stdout.buffer.write(struct.pack("!I", len(reply)) + reply)
        sys.stdout.buffer.flush()
