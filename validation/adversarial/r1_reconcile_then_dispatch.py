"""R1: a reserved-but-not-yet-dispatched token is still dispatched after the intent was (truthfully) reconciled as
not_applied and a retry was executed -> two physical effects for one intent line."""
import sys, contextlib
import pathlib; _r = pathlib.Path(__file__).resolve().parents[2]; sys.path.insert(0, str(_r / "tests")); sys.path.insert(0, str(_r))
from fixture import World, T0, Refused

ARGS = {"pr": "42", "method": "squash"}
w = World()
gid, t = w.grant("agent", ["effect:merge"], ["repo:pr:*"], T0 + 1)
rid, t = w.grant("readback", ["reconcile"], ["repo:pr:*"], t)
w.tick(t); t += 1
iid = w.add("intent", "agent", t, under=gid, op="merge", args=ARGS)
calls = []
g1 = w.guard(lambda *a: calls.append(("g1",) + a) or "ok")
g1.issue(iid, t + 1)
tid = w.state["token_of"][iid]

g2 = w.guard(lambda *a: calls.append(("g2",) + a) or "ok", journal=w.other_journal())
orig_gate = w.journal.effect_gate
state = {"done": False}

@contextlib.contextmanager
def racing_gate():
    # Window between the committed reservation and the physical dispatch (another process holds the write lock,
    # or the guard is slow). Nothing has been sent yet, so a provider readback truthfully says "not applied".
    if not state["done"]:
        state["done"] = True
        s = w.state
        at = s["last_at"] + 1
        w.add("reconciliation", "readback", at, under=rid, intent=iid, result="not_applied")
        retry = w.add("intent", "agent", at + 1, under=gid, op="merge", args=ARGS, retry_of=iid)
        g2.issue(retry, at + 2)
        g2.redeem(w.state["token_of"][retry], at + 3)
    with orig_gate() as st:
        yield st

w.journal.effect_gate = racing_gate
try:
    g1.redeem(tid, t + 2)
    print("first redeem returned normally")
except Refused as r:
    print("first redeem raised after dispatch:", r.code, r.detail)
print("physical calls:", calls)
print("executed:", dict(w.state["executed"]))
assert len(calls) == 2, "expected the double effect"
print("CONFIRMED: two physical merges of repo:pr:42 for one intent line")
