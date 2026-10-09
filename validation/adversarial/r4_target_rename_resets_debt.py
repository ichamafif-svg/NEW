"""R4: renaming a client target (same resource, property, contract otherwise) drops the open gap and opens a fresh one:
the deadline moves and an imminent escalation disappears. Accountability evaluated directly (no sandbox)."""
import sys, copy
import pathlib; _r = pathlib.Path(__file__).resolve().parents[2]; sys.path.insert(0, str(_r / "tests")); sys.path.insert(0, str(_r))
from fixture import World, T0, DAY, H, make_law
from tcb import audit, Accountability
from tcb.canon import parse

def verdict(w, required_at=None):
    s = w.state
    rows = [parse(r) for r in w.journal.raw_rows(0, s["size"], 10**6)]
    return audit(w.kernel, Accountability(w.kernel), rows, genesis_pin=w.journal.genesis_pin,
                 checkpoints=[{"size": s["size"], "head": s["head"]}], required_at=required_at)

def gap(v, name):
    for o in v["open"] + v["escalated"]:
        if o["obligation"] == name:
            return {k: o.get(k) for k in ("opened", "due", "escalated_to")}

for rename in (False, True):
    w = World()
    gid, t = w.grant("ci", ["observe", "certify:real"], ["repo:*"], T0 + 1)
    w.add("observation", "ci", t, under=gid, resource="repo:inventory:all", property="coverage", status="complete", level="real")
    t = T0 + DAY - 2 * H
    w.tick(t)
    w.add("observation", "ci", t + 1, under=gid, resource="repo:inventory:all", property="coverage", status="complete", level="real")
    t += 2
    law = copy.deepcopy(w.law)
    law["targets"][0]["due_ms"] = DAY        # unchanged value, just show both variants go through the same law path
    if rename:
        law["targets"][0]["id"] = "pr42-ci-renamed"
    _, t = w.widen("law", t + 1, release=law)
    w.tick(T0 + DAY + H)                     # past the original deadline
    v = verdict(w)
    name = "target:pr42-ci-renamed" if rename else "target:pr42-ci"
    print("rename" if rename else "no rename", "->", v["state"], name, gap(v, name))
