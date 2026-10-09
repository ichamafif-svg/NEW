"""R5: the floor F1 discharges proof:* only with evidence of level >= real. A client law adds its own evidence kind
whose discharge rule accepts level 'unknown'; compose() accepts it and proof obligations close at the lowest level."""
import sys
import pathlib; _r = pathlib.Path(__file__).resolve().parents[2]; sys.path.insert(0, str(_r / "tests")); sys.path.insert(0, str(_r))
from fixture import World, T0, make_law
from tcb.floors import FLOORS

law = make_law()
law["evidence"] = {"weak": {"fields": {"under": "id", "resource": "resource", "subject": "id", "level": "str"}}}
law["discharges"] = {"weak": [{"obligation": "proof", "key": "subject", "min_level": "unknown"}]}
w = World(law=law)
print("floor discharge:", FLOORS["discharges"])
gid, t = w.grant("agent", ["effect:merge"], ["repo:pr:*"], T0 + 1)
rid, t = w.grant("readback", ["weak", "certify:unknown"], ["repo:pr:*"], t)
iid = w.add("intent", "agent", t, under=gid, op="merge", args={"pr": "42", "method": "squash"})
g = w.guard(lambda *a: "ok"); g.issue(iid, t + 1); g.redeem(w.state["token_of"][iid], t + 2)
assert f"proof:{iid}" in w.state["obligations"]
w.add("weak", "readback", w.state["last_at"] + 1, under=rid, resource="repo:pr:42", subject=iid, level="unknown")
print("proof obligation still open:", f"proof:{iid}" in w.state["obligations"])
