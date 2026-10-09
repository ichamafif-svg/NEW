"""R6: obligations.key_of (kernel) and invariants._key disagree on a `where` clause with a boolean on a dotted path.
The kernel silently skips the gate (admits a gated intent); the second judge sees the gate and halts the journal.
Any agent holding the capability can thus trigger a persistent halt that blocks every later write, freezes included."""
import sys
import pathlib; _r = pathlib.Path(__file__).resolve().parents[2]; sys.path.insert(0, str(_r / "tests")); sys.path.insert(0, str(_r))
from fixture import World, T0, DAY, Refused, make_law
from tcb import Kernel, empty

law = make_law()
law["ops"] = {"deploy": {"args": {"env": "segment", "force": "bool"}, "resource": "repo:deploy:{env}", "profile": "capability"}}
law["obligations"] = [{"id": "force-approval", "level": "refuse", "due_ms": DAY, "on_due": "lapse",
                       "open": [{"kind": "flag", "key": "intent"}],
                       "gate": [{"kind": "intent", "op": "deploy", "key": "args.env", "where": {"args.force": True}}]}]
w = World(law=law)
gid, t = w.grant("agent", ["effect:deploy"], ["repo:deploy:*"], T0 + 1)

# 1) the kernel alone admits the gated intent (gate bypass)
e, _ = w.signed("intent", "agent", t, under=gid, op="deploy", args={"env": "prod", "force": True})
print("kernel alone:", w.kernel.admit(w.journal.state, e))
# 2) through the journal, the second judge disagrees -> persistent halt
try:
    w.journal.append(e)
except Refused as r:
    print("journal:", r.code, r.detail)
try:
    w.add("freeze", "sentinel", t + 1, scope="repo:*")
except Refused as r:
    print("later freeze:", r.code, r.detail)
print("pin store halt:", w.pins.halted())
