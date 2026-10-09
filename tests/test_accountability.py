"""The accountability silo: one stable obligation per target, independent sources, escalation, silent witness, and
isolation from admission."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixture import DAY, H, T0, Refused, World, make_law, raises, run  # noqa: E402
from tcb import audit  # noqa: E402
from tcb.sandbox import WorkerFault
from unittest.mock import patch


def ci(w, t):
    gid, t = w.grant("ci", ["observe", "certify:real"], ["repo:*"], t)
    return gid, t


def observe(w, gid, at, resource, prop, status, author="ci"):
    return w.add("observation", author, at, under=gid, resource=resource, property=prop, status=status, level="real")


def health(w, **kw):
    s = w.state
    w.pins.retain({"size": s["size"], "head": s["head"]})
    return w.journal.health(**kw)


def obligation(w, name):
    h = health(w)
    return next(o for o in h["open"] + h["escalated"] if o["obligation"] == name)


def test_every_target_starts_open_and_coverage_gates_property():
    w = World()
    gid, t = ci(w, T0 + 1)
    h = health(w)
    assert h["state"] == "IN_PROGRESS" and {"target:inventory", "target:pr42-ci"} <= {o["obligation"] for o in h["open"]}
    observe(w, gid, t, "repo:pr:42", "ci", "green")
    h = health(w)
    pr = next(o for o in h["open"] if o["obligation"] == "target:pr42-ci")
    assert pr["needs"] == ["cover"], pr                              # proven property, but its inventory is not
    observe(w, gid, t + 1, "repo:inventory:all", "coverage", "complete")
    observe(w, gid, t + 2, "repo:pr:42", "ci", "green")
    assert health(w)["state"] == "PROVEN"


def test_repeated_bad_observations_never_postpone_the_deadline():
    w = World()
    gid, t = ci(w, T0 + 1)
    observe(w, gid, t, "repo:inventory:all", "coverage", "complete")
    observe(w, gid, t + 1, "repo:pr:42", "ci", "red")
    due = obligation(w, "target:pr42-ci")["due"]
    for i in range(3):
        w.tick(t + (i + 1) * H)
        observe(w, gid, t + (i + 1) * H + 1, "repo:pr:42", "ci", "red")
    assert obligation(w, "target:pr42-ci")["due"] == due


def test_only_an_independent_declared_source_closes_a_target():
    w = World(law=make_law(owner="agent"))
    agent_gid, t = w.grant("agent", ["observe", "certify:real"], ["repo:pr:*"], T0 + 1)
    observe(w, agent_gid, t, "repo:pr:42", "ci", "green", author="agent")       # the owner is not a source
    rb, t = w.grant("readback", ["observe", "certify:real"], ["repo:pr:*"], t + 1)
    observe(w, rb, t, "repo:pr:42", "ci", "green", author="readback")           # not a declared source
    # ci, but delegated by the owner: shares a holder with the owner's label
    via = w.add("delegate", "agent", t + 1, parent=agent_gid, holder="ci", actions=["observe", "certify:real"],
                resources=["repo:pr:42"], conditions=[], not_after=T0 + 20 * DAY)
    observe(w, via, t + 2, "repo:pr:42", "ci", "green")
    assert "pr42-ci" not in {p["target"] for p in health(w)["proven"]}
    own, t = ci(w, t + 3)
    observe(w, own, t, "repo:inventory:all", "coverage", "complete")
    evidence = observe(w, own, t + 1, "repo:pr:42", "ci", "green")
    assert {"target": "pr42-ci", "evidence": evidence} in health(w)["proven"]


def test_overdue_gap_escalates_and_expiry_opens_at_expiry():
    w = World(law=make_law(fresh_ms=2 * H, due_ms=H))
    gid, t = ci(w, T0 + 1)
    observe(w, gid, t, "repo:inventory:all", "coverage", "complete")
    observe(w, gid, t + 1, "repo:pr:42", "ci", "green")
    assert health(w)["state"] == "PROVEN"
    w.tick(t + 10 * H)
    w.add("heartbeat", "sentinel", t + 10 * H + 1, seen=0)
    ob = obligation(w, "target:pr42-ci")
    assert ob["opened"] == t + 2 * H + 1        # coverage expires first; that gap also blocks the property
    h = health(w)
    assert h["state"] == "ESCALATED" and h["escalated"][0]["escalated_to"] == ["alice", "bob", "carol", "dave"]


def test_a_silent_witness_cannot_hold_the_verdict():
    w = World()
    h = health(w, required_at=T0 + 30 * DAY)
    assert h["state"] == "ESCALATED", h["state"]
    assert any(o["obligation"] == "clock:after-ledger" for o in h["open"] + h["escalated"])


def test_silent_witness_expires_previously_proven_targets_without_moving_ledger():
    w = World(law=make_law(fresh_ms=2 * H, due_ms=H))
    gid, t = ci(w, T0 + 1)
    observe(w, gid, t, "repo:inventory:all", "coverage", "complete")
    observe(w, gid, t + 1, "repo:pr:42", "ci", "green")
    assert health(w)["state"] == "PROVEN"
    before = w.state["head"]
    h = health(w, required_at=t + 5 * H)
    assert h["state"] == "ESCALATED" and not h["proven"]
    assert {"target:inventory", "target:pr42-ci"} <= {o["obligation"] for o in h["escalated"]}
    property_gap = next(o for o in h["escalated"] if o["obligation"] == "target:pr42-ci")
    assert property_gap["opened"] == t + 2 * H + 1
    assert w.state["head"] == before and h["as_of"] == t + 1


def test_lapsing_stages_never_escalate_but_reconcile_does():
    w = World()
    gid, t = w.grant("agent", ["effect:merge"], ["repo:pr:*"], T0 + 1)
    iid = w.add("intent", "agent", t, under=gid, op="merge", args={"pr": "42", "method": "squash"})
    h = health(w, required_at=t + 3 * DAY)
    assert f"pending:{iid}" not in {o["obligation"] for o in h["escalated"]}
    g = w.guard(lambda *a: "unknown")
    g.issue(iid, t + 1)
    g.redeem(w.state["token_of"][iid], t + 2)
    h = health(w, required_at=t + 3 * DAY)
    assert f"reconcile:{iid}" in {o["obligation"] for o in h["escalated"]}


def test_a_fault_in_accountability_never_blocks_admission():
    w = World()
    def broken(*a):
        raise RuntimeError("bug in the silo")
    w.acc.feed = broken
    w.add("freeze", "sentinel", T0 + 1, scope="repo:x:*")             # admitted anyway
    # The journal never executes the supplied object's code.
    assert health(w)["state"] == "IN_PROGRESS"
    with patch("tcb.sandbox.StreamWorker.request", side_effect=WorkerFault("worker unavailable")):
        assert health(w)["state"] == "FAULT"
        w.add("heartbeat", "sentinel", T0 + 2, seen=0)


def test_external_audit_replays_and_checks_pins():
    w = World()
    gid, t = ci(w, T0 + 1)
    import sqlite3
    from tcb.canon import parse
    rows = [parse(r) for (r,) in sqlite3.connect(w.path).execute("SELECT raw FROM entries ORDER BY seq")]
    s = w.state
    v = audit(w.kernel, w.acc, rows, genesis_pin=s["domain"], checkpoints=[{"size": s["size"], "head": s["head"]}])
    assert v["state"] == "IN_PROGRESS"
    with raises(Refused, "HIST.ROLLBACK"):
        audit(w.kernel, w.acc, rows[:-1], genesis_pin=s["domain"], checkpoints=[{"size": s["size"], "head": s["head"]}])


if __name__ == "__main__":
    run(globals())
