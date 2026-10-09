"""The effect line: single use across guards and restarts, current authority at the point of use, crash recovery,
independent proof, budgets, lapse, silent controls."""
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixture import DAY, H, MIN, T0, Refused, World, make_law, raises, run  # noqa: E402

ARGS = {"pr": "42", "method": "squash"}


def ready(w, **grant):
    gid, t = w.grant("agent", ["effect:merge"], ["repo:pr:*"], T0 + 1, **grant)
    rid, t = w.grant("readback", ["evidence", "reconcile", "observe", "certify:real"], ["repo:pr:*"], t)
    return gid, rid, t


def test_two_guards_and_restart_run_only_once():
    w = World()
    gid, _, t = ready(w)
    iid = w.add("intent", "agent", t, under=gid, op="merge", args=ARGS)
    calls = []
    g1 = w.guard(lambda *a: calls.append(a) or "ok")
    tok = g1.issue(iid, t + 1)["envelope"]
    tid = w.state["token_of"][iid]
    g2 = w.guard(lambda *a: calls.append(a) or "ok", journal=w.other_journal())

    def attempt(g):
        try:
            g.redeem(tid, t + 2)
            return "ran"
        except Refused as r:
            return r.code
    with ThreadPoolExecutor(2) as pool:
        results = sorted(pool.map(attempt, [g1, g2]))
    assert results.count("ran") == 1 and set(results) - {"ran"} <= {"OBL.NOT_OPEN", "HIST.TIME"}, results
    restarted = w.guard(lambda *a: calls.append(a) or "ok", journal=w.other_journal())
    with raises(Refused, "OBL.NOT_OPEN"):
        restarted.redeem(tid, t + 10)
    assert calls == [("merge", "repo:pr:42", ARGS)], calls
    assert tok


def test_revoke_before_reservation_prevents_execution():
    w = World()
    gid, _, t = ready(w)
    iid = w.add("intent", "agent", t, under=gid, op="merge", args=ARGS)
    g = w.guard(lambda *a: "ok")
    g.issue(iid, t + 1)
    w.add("revoke", "carol", t + 2, grant=gid)
    with raises(Refused, "CAP.WITHDRAWN"):
        g.redeem(w.state["token_of"][iid], t + 3)


def test_freeze_after_token_blocks_reservation():
    w = World()
    gid, _, t = ready(w)
    iid = w.add("intent", "agent", t, under=gid, op="merge", args=ARGS)
    g = w.guard(lambda *a: "ok")
    g.issue(iid, t + 1)
    w.add("freeze", "sentinel", t + 2, scope="repo:pr:*")
    with raises(Refused, "FREEZE.ACTIVE"):
        g.redeem(w.state["token_of"][iid], t + 3)


def test_crash_after_reservation_requires_independent_reconciliation():
    w = World()
    gid, rid, t = ready(w)
    w_agent_rec, _ = w.grant("agent", ["reconcile"], ["repo:pr:*"], t)
    t += 2 * H
    w.tick(t)
    iid = w.add("intent", "agent", t + 1, under=gid, op="merge", args=ARGS)
    g = w.guard(lambda *a: (_ for _ in ()).throw(RuntimeError("network")))
    g.issue(iid, t + 2)
    g.redeem(w.state["token_of"][iid], t + 3)                      # executor raised: outcome unknown
    assert f"reconcile:{iid}" in w.state["obligations"]
    w.refuse("OBL.BLOCKED", "intent", "agent", t + 5, under=gid, op="merge", args=ARGS, retry_of=iid)
    w.refuse("PROV.NOT_INDEPENDENT", "reconciliation", "agent", t + 6, under=w_agent_rec, intent=iid, result="not_applied")
    w.tick(t + 2 * DAY)                                           # a reconcile obligation never lapses
    assert f"reconcile:{iid}" in w.state["obligations"]
    w.add("reconciliation", "readback", t + 2 * DAY + 1, under=rid, intent=iid, result="not_applied")
    w.add("intent", "agent", t + 2 * DAY + 2, under=gid, op="merge", args=ARGS, retry_of=iid)


def test_proof_names_its_intent_and_exact_resource():
    w = World()
    gid, rid, t = ready(w)
    iid = w.add("intent", "agent", t, under=gid, op="merge", args=ARGS)
    g = w.guard(lambda *a: "ok")
    g.issue(iid, t + 1)
    g.redeem(w.state["token_of"][iid], t + 2)
    assert f"proof:{iid}" in w.state["obligations"]
    later = w.state["last_at"] + 1
    w.refuse("PROV.SUBJECT", "evidence", "readback", later, under=rid, resource="repo:pr:43", subject=iid, level="real")
    w.refuse("NIV.UNKNOWN", "evidence", "readback", later, under=rid, resource="repo:pr:42", subject=iid, level="fake")
    w.add("evidence", "readback", later + 1, under=rid, resource="repo:pr:42", subject=iid, level="real")
    assert f"proof:{iid}" not in w.state["obligations"]


def test_budget_counts_tokens_along_the_chain():
    w = World()
    gid, _, t = ready(w, budget={"count": 1, "window": DAY})
    a = w.add("intent", "agent", t, under=gid, op="merge", args=ARGS)
    b = w.add("intent", "agent", t + 1, under=gid, op="merge", args={"pr": "43", "method": "squash"})
    g = w.guard(lambda *x: "ok")
    g.issue(a, t + 2)
    with raises(Refused, "OBL.BUDGET"):
        g.issue(b, t + 3)


def test_time_lapses_unused_authority():
    w = World()
    gid, _, t = ready(w)
    iid = w.add("intent", "agent", t, under=gid, op="merge", args=ARGS)
    g = w.guard(lambda *a: "ok")
    g.issue(iid, t + 1)
    w.tick(t + DAY + 2)
    with raises(Refused, "OBL.LAPSED"):                           # an old token cannot be redeemed
        g.redeem(w.state["token_of"][iid], t + DAY + 3)
    w.add("intent", "agent", t + DAY + 4, under=gid, op="merge", args=ARGS, retry_of=iid)   # nothing blocks a retry


def test_silent_sentinel_requires_a_human_cosignature():
    w = World(law=make_law(heartbeat_ms=10 * MIN))
    gid, _, t = ready(w)
    iid = w.add("intent", "agent", t, under=gid, op="merge", args=ARGS)
    g = w.guard(lambda *a: "ok")
    with raises(Refused, "FLOOR0.PRUDENT"):
        g.issue(iid, t + 1)
    w.add("heartbeat", "sentinel", t + 2, seen=0)
    g.issue(iid, t + 3)
    flagged = w.add("intent", "agent", t + 4, under=gid, op="merge", args={"pr": "9", "method": "squash"})
    w.add("flag", "sentinel", t + 5, intent=flagged)
    with raises(Refused, "FLOOR0.PRUDENT"):
        g.issue(flagged, t + 6)
    g.issue(flagged, t + 7, cosigners=[w.cosigner("carol")])


if __name__ == "__main__":
    run(globals())
