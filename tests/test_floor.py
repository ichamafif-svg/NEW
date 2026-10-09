"""F0-2, F0-3 and F0-10: no single code, pinned code, pins at every write. Each test simulates the failure of one
mechanism and checks that another one catches it."""
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixture import DAY, H, T0, Refused, World, digest, raises, run  # noqa: E402
from tcb import invariants as inv_mod  # noqa: E402

ARGS = {"pr": "42", "method": "squash"}


def test_restoring_a_journal_backup_cannot_erase_a_revocation():
    w = World()
    gid, t = w.grant("agent", ["effect:merge"], ["repo:pr:*"], T0 + 1)
    calls = []
    g = w.guard(lambda *a: calls.append(a) or "ok")
    i2 = w.add("intent", "agent", t, under=gid, op="merge", args={"pr": "43", "method": "squash"})
    g.issue(i2, t + 1)
    shutil.copy(w.path, w.tmp / "backup.sqlite3")
    w.add("revoke", "carol", t + 2, grant=gid)
    shutil.copy(w.tmp / "backup.sqlite3", w.path)
    with raises(ValueError, "truncated"):
        w.other_journal().snapshot()
    assert not calls


def test_the_genesis_pins_the_tcb_code():
    w = World(genesis=False)
    w.refuse("CODE.MISMATCH", "genesis", "alice", T0, ["alice", "bob"], root=w.root, law=w.law,
             code=digest({"another": "build"}))


def test_kernel_bug_is_caught_by_the_invariants_and_halts():
    w = World()
    gid, t = w.grant("agent", ["effect:merge"], ["repo:pr:7"], T0 + 1)
    original = w.kernel._delegate
    def buggy(s, b, signers, d):                       # a kernel that forgot to check attenuation
        d.append(("put", "grants", b["id"], w.kernel._grant_record(b, b["parent"], b["at"])))
    w.kernel._delegate = buggy
    w.refuse("HALT.DISAGREEMENT", "delegate", "agent", t, parent=gid, holder="agent", actions=["effect:merge"],
             resources=["repo:*"], conditions=[], not_after=T0 + 20 * DAY)
    w.kernel._delegate = original
    assert gid in w.journal.state["grants"] and len(w.journal.state["grants"]) == 1
    frozen, _ = w.signed("freeze", "carol", t + 1, scope="repo:x:*", state=w.journal.state)
    with raises(Refused, "HALT"):
        w.journal.append(frozen)
    with raises(Refused, "HALT"):
        w.other_journal().append(frozen)   # the halt is durable


def test_kernel_bug_on_delay_is_caught():
    w = World()
    pid = w.add("grant", "alice", T0 + 1, ["alice", "bob"], holder="agent", actions=["effect:merge"],
                resources=["repo:pr:*"], conditions=[], not_after=T0 + 30 * DAY)
    w.kernel.law_of(w.state).delay = {k: 1 for k in w.kernel.law_of(w.state).delay}  # the kernel's view of the law is corrupted in memory
    w.refuse("WIDEN.DELAY", "activate", "alice", T0 + 2, ["alice", "bob"], proposal=pid)   # recorded at proposal time
    original = w.kernel._activate
    def buggy(s, b, signers, d):
        p = s["proposals"][b["proposal"]]
        d += [("put", "grants", p["id"], w.kernel._grant_record(p["body"], "root", b["at"])), ("drop", "proposals", p["id"])]
    w.kernel._activate = buggy
    w.refuse("HALT.DISAGREEMENT", "activate", "alice", T0 + 3, ["alice", "bob"], proposal=pid)
    w.kernel._activate = original


def test_double_reservation_is_refused_by_the_store_when_both_checks_fail():
    w = World()
    gid, t = w.grant("agent", ["effect:merge"], ["repo:pr:*"], T0 + 1)
    iid = w.add("intent", "agent", t, under=gid, op="merge", args=ARGS)
    calls = []
    g = w.guard(lambda *a: calls.append(a) or "ok")
    g.issue(iid, t + 1)
    tid = w.state["token_of"][iid]
    g.redeem(tid, t + 2)
    w.kernel._consume = lambda s, d, name, at: None                              # kernel bug: tokens reusable
    w.kernel._line = lambda *a: None                                             # and the effect line disabled
    saved = inv_mod.Invariants._reservation, inv_mod.Invariants._obligations, inv_mod.Invariants._line
    inv_mod.Invariants._reservation = lambda *a: None                            # and an invariant bug
    inv_mod.Invariants._obligations = lambda *a: None
    inv_mod.Invariants._line = lambda *a: None
    try:
        with raises(Refused, "HALT.DISAGREEMENT"):
            g.redeem(tid, w.state["last_at"] + 1)
    finally:
        inv_mod.Invariants._reservation, inv_mod.Invariants._obligations, inv_mod.Invariants._line = saved
    assert len(calls) == 1


def test_invariant_checker_crash_halts():
    w = World()
    w.journal.invariants.check = lambda *a: 1 / 0
    w.refuse("HALT.DISAGREEMENT", "freeze", "carol", T0 + 1, scope="repo:x:*")


def test_provider_gets_a_stable_key_per_reservation():
    w = World()
    gid, t = w.grant("agent", ["effect:merge"], ["repo:pr:*"], T0 + 1)
    iid = w.add("intent", "agent", t, under=gid, op="merge", args=ARGS)
    from tcb.effects import EffectPort
    from tcb.guard import Guard
    seen = []
    g = Guard(w.journal, "guard", w.cosigner("guard"), EffectPort({
        "merge": lambda resource, args, reservation_key: seen.append(reservation_key) or "ok"}))
    g.issue(iid, t + 1)
    tid = w.state["token_of"][iid]
    g.redeem(tid, t + 2)
    assert seen == [digest({"genesis": w.state["domain"], "reservation": w.state["reserved"][tid]})]


def test_health_answers_on_a_long_journal():
    w = World()
    at = T0
    while w.state["size"] < 2000:
        at += 1
        w.add("heartbeat", "sentinel", at, seen=0)
        if w.state["size"] % 250 == 0:
            at += 1
            w.tick(at)
    started = time.time()
    h = w.journal.health()
    assert h["state"] != "FAULT", h
    print(f"     health on {w.state['size']} entries: {time.time() - started:.2f}s")


if __name__ == "__main__":
    run(globals())
