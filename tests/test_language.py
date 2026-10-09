"""One language, three levels: the same obligation declaration refuses, escalates or measures; fresh independent counting is
allowed everywhere; negation is rejected at every level; the invariants re-check law obligations independently."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixture import DAY, H, T0, Kernel, World, digest, make_law, raises, run  # noqa: E402
from tcb.law import LawError  # noqa: E402

EVIDENCE = {
    "signal": {"fields": {"under": "id", "resource": "resource", "key": "id"}},
    "verdict": {"fields": {"under": "id", "resource": "resource", "workitem": "id", "result": "str"}},
    "escalation": {"fields": {"under": "id", "resource": "resource", "workitem": "id"}},
    "resolution": {"fields": {"under": "id", "resource": "resource", "workitem": "id"}},
}
OPS = {"fix": {"args": {"wi": "segment", "pr": "segment"}, "resource": "repo:pr:{pr}", "profile": "capability"}}


def workitem(level, **extra):
    return {"id": "workitem", "level": level, "due_ms": DAY, "on_due": "escalate",
            "open": [{"kind": "signal", "key": "key"}],
            "close": [{"kind": "verdict", "key": "workitem", "where": {"result": "pass"}}],
            "gate": [{"kind": "intent", "op": "fix", "key": "args.wi"}], **extra}


def world(*decls, conditions=None):
    law = make_law(ops=OPS, evidence=EVIDENCE, obligations=list(decls))
    if conditions:
        law["conditions"] = {**law.get("conditions", {}), **conditions}
    w = World(law=law)
    ci, t = w.grant("ci", ["signal", "verdict"], ["repo:*"], T0 + 1)
    return w, ci, t


def health(w, **kw):
    return w.journal.health(**kw)


def test_the_same_gate_refuses_escalates_or_measures():
    # refuse: the kernel will not let work start without an open WorkItem
    w, ci, t = world(workitem("refuse"))
    gid, t = w.grant("agent", ["effect:fix"], ["repo:pr:*"], t)
    fix = {"wi": "wi-1", "pr": "7"}
    w.refuse("OBL.GATE", "intent", "agent", t, under=gid, op="fix", args=fix)
    w.add("signal", "ci", t + 1, under=ci, resource="repo:pr:7", key="wi-1")
    w.add("intent", "agent", t + 2, under=gid, op="fix", args=fix)
    w.add("verdict", "ci", t + 3, under=ci, resource="repo:pr:7", workitem="wi-1", result="pass")
    w.refuse("OBL.GATE", "intent", "agent", t + 4, under=gid, op="fix", args=fix)       # closed: no more work on it
    assert "workitem:wi-1" in w.state["closed"]

    # escalate: the entry is admitted, the violation escalates at once
    w, ci, t = world(workitem("escalate"))
    gid, t = w.grant("agent", ["effect:fix"], ["repo:pr:*"], t)
    w.add("intent", "agent", t, under=gid, op="fix", args=fix)
    h = health(w)
    assert h["state"] == "ESCALATED" and any(o["obligation"].startswith("violation:workitem:") for o in h["escalated"])

    # measure: admitted, counted, never escalated
    w, ci, t = world(workitem("measure"))
    gid, t = w.grant("agent", ["effect:fix"], ["repo:pr:*"], t)
    w.add("intent", "agent", t, under=gid, op="fix", args=fix)
    h = health(w)
    assert h["measured"]["workitem"]["violations"] == 1
    assert not any(o["obligation"].startswith("violation:") for o in h["escalated"])


def test_one_instance_per_key_and_deadline_escalates():
    w, ci, t = world(workitem("refuse"))
    w.add("signal", "ci", t, under=ci, resource="repo:pr:7", key="wi-1")
    opened = w.state["obligations"]["workitem:wi-1"]["opened"]
    w.add("signal", "ci", t + 1, under=ci, resource="repo:pr:7", key="wi-1")             # redelivered: kept
    assert w.state["obligations"]["workitem:wi-1"]["opened"] == opened
    h = health(w, required_at=opened + DAY + 1)
    assert any(o["obligation"] == "workitem:wi-1" for o in h["escalated"])


def test_negation_is_rejected_at_every_level():
    quiet = {"rules": [{"head": ["ok", []], "body": [["at", ["?t"]], ["not", "open", ["escalation", "wi-1"]]]}]}
    for level in ("refuse", "escalate", "measure"):
        law = make_law(ops=OPS, evidence=EVIDENCE, obligations=[workitem(level, when=quiet["rules"])])
        with raises(LawError, "condition"):
            Kernel().load(law)


def test_fresh_independent_closures_authorize_at_refuse():
    earned = {"all": [{"closed_at_least": ["workitem", 2]}]}
    w, ci, t = world(workitem("refuse"), conditions={"earned": earned})
    gid, t = w.grant("agent", ["effect:merge"], ["repo:pr:*"], t, conditions=["earned"])
    args = {"pr": "9", "method": "squash"}
    for i in range(2):
        w.refuse("LAW.CONDITION", "intent", "agent", t, under=gid, op="merge", args=args)
        w.add("signal", "ci", t + 1, under=ci, resource="repo:pr:9", key=f"wi-{i}")
        w.add("verdict", "ci", t + 2, under=ci, resource="repo:pr:9", workitem=f"wi-{i}", result="pass")
        t += 3
    w.add("intent", "agent", t, under=gid, op="merge", args=args)


def test_prefix_in_conditions():
    protect = {"all": [{"prefix": ["args.pr", "4"]}]}
    w, ci, t = world(conditions={"forties": protect})
    gid, t = w.grant("agent", ["effect:merge"], ["repo:pr:*"], t, conditions=["forties"])
    w.add("intent", "agent", t, under=gid, op="merge", args={"pr": "42", "method": "squash"})
    w.refuse("LAW.CONDITION", "intent", "agent", t + 1, under=gid, op="merge", args={"pr": "52", "method": "squash"})


def test_invariants_catch_a_kernel_that_skips_a_law_gate():
    w, ci, t = world(workitem("refuse"))
    gid, t = w.grant("agent", ["effect:fix"], ["repo:pr:*"], t)
    w.kernel._law_obligations = lambda *a: None
    w.refuse("HALT.DISAGREEMENT", "intent", "agent", t, under=gid, op="fix", args={"wi": "wi-1", "pr": "7"})


if __name__ == "__main__":
    run(globals())
