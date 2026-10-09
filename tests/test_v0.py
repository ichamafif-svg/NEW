"""V0 guarantee probes: sealed routes, current human authority and independent finite policies."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixture import World, T0, H, DAY, Refused, make_law, Kernel, digest, raises, run, copy
from tcb import policy
from test_language import world, workitem

ARGS = {"pr": "7", "method": "squash"}


def sensitive_world():
    law = make_law(ops={"release": {"args": {"pr": "segment", "method": "str"}, "resource": "repo:pr:{pr}",
                                    "profile": "human_quorum"}})
    w = World(law=law)
    gid, t = w.grant("agent", ["effect:release"], ["repo:pr:*"], T0 + 1)
    return w, w.add("intent", "agent", t, under=gid, op="release", args=ARGS), t


def test_sensitive_profile_requires_quorum_and_cannot_be_selected_by_the_actor():
    w, iid, t = sensitive_world()
    calls = []
    guard = w.guard(lambda *args: calls.append(args) or "ok")
    for co in ([], [w.cosigner("alice")]):
        with raises(Refused, "PROFILE.QUORUM"):
            guard.issue(iid, t + 1, co)
    guard.issue(iid, t + 1, [w.cosigner("alice"), w.cosigner("bob")])
    guard.redeem(w.state["token_of"][iid], t + 2)
    assert len(calls) == 1
    law = make_law(ops={"release": {"args": {"pr": "segment"}, "resource": "repo:pr:{pr}", "profile": "anything"}})
    with raises(Exception, "profile"):
        Kernel().load(law)


def test_old_quorum_cannot_authorize_after_root_rotation():
    w, iid, t = sensitive_world()
    guard = w.guard(lambda *args: (_ for _ in ()).throw(AssertionError("must not dispatch")))
    guard.issue(iid, t + 1, [w.cosigner("alice"), w.cosigner("bob")])
    tid = w.state["token_of"][iid]
    root = copy.deepcopy(w.root)
    root["identities"].pop("sentinel")
    _, t = w.widen("rotate", t + 2, root=root)
    with raises(Refused, "PROFILE.QUORUM"):
        guard.redeem(tid, t)


def test_single_profile_bug_is_detected_by_the_second_checker():
    w, iid, t = sensitive_world()
    w.kernel._profile = lambda *args: None
    with raises(Refused, "HALT.DISAGREEMENT"):
        w.guard(lambda *args: "ok").issue(iid, t + 1)
    assert w.pins.halted()


def test_single_policy_evaluator_bug_is_detected():
    w = World()
    gid, t = w.grant("agent", ["effect:merge"], ["repo:pr:*"], T0 + 1, conditions=["bot-author"])
    original = policy.evaluate
    policy.evaluate = lambda *args, **kwargs: True
    try:
        w.refuse("HALT.DISAGREEMENT", "intent", "agent", t, under=gid, op="merge", args=ARGS)
    finally:
        policy.evaluate = original
    assert w.pins.halted()


def test_dispatch_checker_detects_a_judge_bug_after_a_revocation():
    w = World()
    gid, t = w.grant("agent", ["effect:merge"], ["repo:pr:*"], T0 + 1)
    iid = w.add("intent", "agent", t, under=gid, op="merge", args=ARGS)
    calls = []
    guard = w.guard(lambda *args: calls.append(args) or "ok")
    guard.issue(iid, t + 1)
    tid = w.state["token_of"][iid]
    transact = w.journal.transact
    def reserve_then_revoke(builder):
        result = transact(builder)
        if result[0]["envelope"] and tid in w.journal.state["reserved"]:
            w.journal.transact = transact
            w.add("revoke", "carol", t + 3, grant=gid)
        return result
    w.journal.transact = reserve_then_revoke
    w.kernel.judge_dispatch = lambda *args: w.journal.state["intents"][iid]
    with raises(Refused, "HALT.DISAGREEMENT"):
        guard.redeem(tid, t + 2)
    assert not calls and w.pins.halted()


def test_self_certified_closures_do_not_earn_autonomy():
    w, ci, t = world(workitem("refuse"), conditions={"earned": {"all": [{"closed_at_least": ["workitem", 2]}]}})
    gid, t = w.grant("agent", ["effect:merge", "verdict"], ["repo:pr:*"], t)
    for i in range(2):
        w.add("signal", "ci", t, under=ci, resource="repo:pr:7", key=f"wi-{i}")
        w.add("verdict", "agent", t + 1, under=gid, resource="repo:pr:7", workitem=f"wi-{i}", result="pass")
        t += 2
    conditioned = w.add("delegate", "agent", t, parent=gid, holder="agent", actions=["effect:merge"],
                        resources=["repo:pr:*"], conditions=["earned"], not_after=T0 + 10 * DAY)
    w.refuse("LAW.CONDITION", "intent", "agent", t + 1, under=conditioned, op="merge", args=ARGS)


def test_actor_cannot_override_a_sealed_effect_profile():
    w, iid, t = sensitive_world()
    gid = w.state["intents"][iid]["under"]
    w.refuse("TYPE.SHAPE", "intent", "agent", t + 1, under=gid, op="release", args=ARGS, profile="capability")


def test_expired_independent_closures_stop_authorizing():
    w, ci, t = world(workitem("refuse"), conditions={"earned": {"all": [{"closed_at_least": ["workitem", 1]}]}})
    gid, t = w.grant("agent", ["effect:merge"], ["repo:pr:*"], t, conditions=["earned"])
    w.add("signal", "ci", t, under=ci, resource="repo:pr:7", key="wi-1")
    w.add("verdict", "ci", t + 1, under=ci, resource="repo:pr:7", workitem="wi-1", result="pass")
    iid = w.add("intent", "agent", t + 2, under=gid, op="merge", args=ARGS)
    calls = []
    guard = w.guard(lambda *args: calls.append(args) or "ok")
    guard.issue(iid, t + 3)
    token = w.state["token_of"][iid]
    expired = t + DAY + 2
    w.tick(expired - 1)
    w.refuse("LAW.CONDITION", "intent", "agent", expired, under=gid, op="merge", args=ARGS)
    with raises(Refused, "LAW.CONDITION"):
        guard.redeem(token, expired)
    assert not calls


if __name__ == "__main__":
    run(globals())
