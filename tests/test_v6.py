"""Adversarial fusion checks: law epochs, target contracts, independent payloads and the physical send boundary."""
import copy
import sys
import threading
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixture import World, T0, H, DAY, Refused, make_law, digest, raises, run
from test_accountability import ci, observe, health, obligation, floors_proven
from test_v0 import sensitive_world
from tcb import Kernel, EffectPort, Guard
from tcb.effects import NotDispatched
from tcb.law import LawError

ARGS = {"pr": "42", "method": "squash"}


def issued(w):
    gid, t = w.grant("agent", ["effect:merge"], ["repo:pr:*"], T0 + 1)
    iid = w.add("intent", "agent", t, under=gid, op="merge", args=ARGS)
    calls = []
    guard = w.guard(lambda *a: calls.append(a) or "ok")
    guard.issue(iid, t + 1)
    return gid, t, iid, guard, calls


def proven():
    w = World()
    gid, t = ci(w, T0 + 1)
    t = floors_proven(w, gid, t)
    observe(w, gid, t, "repo:inventory:all", "coverage", "complete")
    observe(w, gid, t + 1, "repo:pr:42", "ci", "green")
    assert health(w)["state"] == "PROVEN"
    return w, gid, t + 1


def test_a_proof_never_moves_to_a_different_resource():
    w, gid, t = proven()
    law = copy.deepcopy(w.law)
    law["targets"][0]["resource"] = "repo:pr:43"
    _, t = w.widen("law", t + 1, release=law)
    assert "pr42-ci" not in {p["target"] for p in health(w)["proven"]}
    observe(w, gid, t, "repo:pr:43", "ci", "green")
    assert health(w)["state"] == "PROVEN"


def test_target_owner_and_source_changes_invalidate_cached_proofs():
    for change in ({"owner": "agent"}, {"sources": ["readback"]}, {"property": "other-ci"}):
        w, gid, t = proven()
        law = copy.deepcopy(w.law)
        law["targets"][0].update(change)
        _, t = w.widen("law", t + 1, release=law)
        assert "pr42-ci" not in {p["target"] for p in health(w)["proven"]}
        assert obligation(w, "target:pr42-ci")["needs"] == ["observe"]


def test_law_change_does_not_postpone_an_existing_gap():
    w = World()
    original = obligation(w, "target:pr42-ci")
    law = copy.deepcopy(w.law)
    law["targets"][0].update(owner="agent", due_ms=H)
    w.widen("law", T0 + 1, release=law)
    current = obligation(w, "target:pr42-ci")
    assert current["opened"] == original["opened"]
    assert current["due"] == original["opened"] + H
    assert current["owner"] == "agent"


def test_every_pending_proposal_is_bound_to_its_law():
    for kind in ("grant", "rotate", "unfreeze"):
        w = World()
        at = T0 + 1
        if kind == "grant":
            fields = dict(holder="agent", actions=["effect:merge"], resources=["repo:pr:*"],
                          conditions=[], not_after=T0 + 30 * DAY)
        elif kind == "rotate":
            root = copy.deepcopy(w.root)
            root["identities"].pop("sentinel")
            fields = dict(root=root)
        else:
            w.add("freeze", "carol", at, scope="repo:pr:*")
            at += 1
            fields = dict(scope="repo:pr:*")
        pid = w.add(kind, "alice", at, ["alice", "bob"], **fields)
        law = copy.deepcopy(w.law)
        law["delays"] = {kind: 2 * H}
        _, t = w.widen("law", at + 1, release=law)
        w.refuse("WIDEN.STALE", "activate", "alice", t, ["alice", "bob"], proposal=pid)


def test_independent_checker_catches_stale_activation_when_kernel_forgets():
    w = World()
    pid = w.add("grant", "alice", T0 + 1, ["alice", "bob"], holder="agent", actions=["effect:merge"],
                resources=["repo:pr:*"], conditions=[], not_after=T0 + 30 * DAY)
    _, t = w.widen("law", T0 + 2, release=make_law(delays={"grant": 2 * H}))
    def buggy(s, b, signers, delta):
        p = s["proposals"][b["proposal"]]
        delta += [("put", "grants", p["id"], w.kernel._grant_record(p["body"], "root", b["at"])),
                  ("drop", "proposals", p["id"])]
    w.kernel._activate = buggy
    w.refuse("HALT.DISAGREEMENT", "activate", "alice", t, ["alice", "bob"], proposal=pid)
    assert w.pins.halted()


def test_invalid_targets_are_refused_before_law_admission():
    for change in ({"fresh_ms": 0}, {"due_ms": 0}, {"coverage": "missing"}, {"min_level": []},
                   {"sources": [["ci"]]}, {"owner": "alice", "sources": ["alice"]}):
        w = World()
        law = copy.deepcopy(w.law)
        law["targets"][0].update(change)
        before = w.state["head"]
        w.refuse("LAW.INVALID", "law", "alice", T0 + 1, ["alice", "bob"], release=law)
        assert before == w.state["head"] and health(w)["state"] != "FAULT"


def test_malformed_composition_maps_never_crash_admission():
    for change in ({"ttl": []}, {"tighten": {"ops": []}}, {"controls": False}):
        w = World()
        law = copy.deepcopy(w.law)
        law.update(change)
        w.refuse("LAW.INVALID", "law", "alice", T0 + 1, ["alice", "bob"], release=law)


def test_changed_operation_contract_invalidates_old_intents_and_tokens():
    law = make_law(ops={"release": {"args": {"pr": "segment", "method": "str"},
                                   "resource": "repo:pr:{pr}", "profile": "capability"}})
    w = World(law=law)
    gid, t = w.grant("agent", ["effect:release"], ["repo:*"], T0 + 1)
    iid = w.add("intent", "agent", t, under=gid, op="release", args=ARGS)
    calls = []
    g = w.guard(lambda *a: calls.append(a) or "ok")
    g.issue(iid, t + 1)
    law = copy.deepcopy(law)
    law["ops"]["release"]["resource"] = "repo:prod:{pr}"
    _, t = w.widen("law", t + 2, release=law)
    with raises(Refused, "LAW.STALE"):
        g.redeem(w.state["token_of"][iid], t)
    assert not calls


def test_changed_condition_does_not_reinterpret_an_old_capability():
    law = make_law(conditions={"restricted": {"all": [{"prefix": ["args.pr", "4"]}]}})
    w = World(law=law)
    gid, t = w.grant("agent", ["effect:merge"], ["repo:pr:*"], T0 + 1, conditions=["restricted"])
    law = copy.deepcopy(law)
    law["conditions"]["restricted"] = {"all": [{"prefix": ["resource", "repo:"]}]}
    _, t = w.widen("law", t, release=law)
    w.refuse("LAW.STALE", "intent", "agent", t, under=gid, op="merge", args=ARGS)


def test_one_corrupted_kernel_profile_does_not_corrupt_both_judges():
    w, iid, t = sensitive_world()
    w.kernel.law_of(w.state).ops["release"]["profile"] = "capability"
    w.kernel._reauthorize = lambda *args: []  # compromise the primary component, not the second judge
    with raises(Refused, "HALT.DISAGREEMENT"):
        w.guard(lambda *a: "ok").issue(iid, t + 1)
    assert w.pins.halted()


def test_dispatch_payload_is_compared_between_both_judges():
    w = World()
    gid, t, iid, guard, calls = issued(w)
    original = w.kernel.judge_dispatch
    def buggy(*args):
        it = copy.deepcopy(original(*args))
        it["args"]["pr"] = "99"
        it["resource"] = "repo:pr:99"
        return it
    w.kernel.judge_dispatch = buggy
    with raises(Refused, "HALT.DISAGREEMENT"):
        guard.redeem(w.state["token_of"][iid], t + 2)
    assert not calls and w.pins.halted()


def test_an_independent_dispatch_checker_crash_halts():
    w = World()
    gid, t, iid, guard, calls = issued(w)
    w.journal.invariants.dispatch = lambda *a: 1 / 0
    with raises(Refused, "HALT.DISAGREEMENT"):
        guard.redeem(w.state["token_of"][iid], t + 2)
    assert not calls and w.pins.halted()


def test_deferred_completion_is_outside_the_gate_and_exceptions_are_unknown():
    w = World()
    gid, t, iid, guard, calls = issued(w)
    def sent(resource, args, key):
        calls.append(key)
        def wait():
            w.add("freeze", "carol", t + 3, scope="repo:pr:*")
            raise NotDispatched("too late to classify as a certain failure")
        return wait
    guard.effect_port = EffectPort({"merge": sent})
    token = w.state["token_of"][iid]
    guard.redeem(token, t + 2)
    assert len(calls) == 1 and w.state["executed"][token] == "unknown"
    assert f"reconcile:{iid}" in w.state["obligations"]
    with raises(Refused, "OBL.NOT_OPEN"):
        guard.redeem(token, w.state["last_at"] + 1)


def test_a_client_can_tighten_a_floor_operation_to_human_quorum():
    w = World(law=make_law(tighten={"ops": {"merge": {"profile": "human_quorum"}}}))
    gid, t = w.grant("agent", ["effect:merge"], ["repo:pr:*"], T0 + 1)
    iid = w.add("intent", "agent", t, under=gid, op="merge", args=ARGS)
    guard = w.guard(lambda *a: "ok")
    with raises(Refused, "PROFILE.QUORUM"):
        guard.issue(iid, t + 1)
    guard.issue(iid, t + 1, [w.cosigner("alice"), w.cosigner("bob")])
    guard.redeem(w.state["token_of"][iid], t + 2)
    with raises(LawError, "only raises"):
        Kernel().load(make_law(tighten={"ops": {"merge": {"profile": "capability"}}}))


def test_request_op_means_the_same_for_both_evaluators():
    w = World(law=make_law(conditions={"merge-only": {"all": [{"eq": ["op", "merge"]}]}}))
    gid, t = w.grant("agent", ["effect:merge"], ["repo:pr:*"], T0 + 1, conditions=["merge-only"])
    iid = w.add("intent", "agent", t, under=gid, op="merge", args=ARGS)
    calls = []
    guard = w.guard(lambda *a: calls.append(a) or "ok")
    guard.issue(iid, t + 1)
    guard.redeem(w.state["token_of"][iid], t + 2)
    assert len(calls) == 1


def test_an_explicit_prefix_audit_never_claims_to_be_current_after_a_write():
    w = World()
    health(w)
    worker = w.journal.auditor._worker
    original = worker.request
    def advance(packet):
        if packet["op"] == "health":
            w.add("freeze", "carol", T0 + 1, scope="repo:pr:*")
        return original(packet)
    with patch.object(worker, "request", side_effect=advance):
        verdict = w.journal.health(prefix=True)
    assert verdict["state"] != "FAULT" and verdict["current"] is False
    assert verdict["head"] != w.state["head"]


def test_activation_is_accounted_under_its_old_law_not_the_new_one():
    w = World()
    law = copy.deepcopy(w.law)
    law["obligations"] = [{"id": "activation-work", "level": "escalate", "due_ms": DAY, "on_due": "escalate",
                           "open": [{"kind": "activate", "key": "proposal"}]}]
    pid, t = w.widen("law", T0 + 1, release=law)
    h = health(w)
    assert not any(o["obligation"] == "activation-work:" + pid for o in h["open"] + h["escalated"])
    grant, t = w.grant("agent", ["effect:merge"], ["repo:pr:*"], t)
    h = health(w)
    assert any(o["obligation"] == "activation-work:" + grant for o in h["open"])


def test_a_repair_route_must_have_compatible_typed_arguments():
    law = make_law(ops={"numeric": {"args": {"pr": "int"}, "resource": "repo:pr:{pr}", "profile": "capability"}})
    law["targets"][0].update(resource="repo:pr:text", repair="numeric")
    with raises(LawError, "F1"):
        Kernel().load(law)
    law["targets"][0]["resource"] = "repo:pr:42"
    Kernel().load(law)


def test_a_repair_route_respects_repeated_argument_values():
    law = make_law(ops={"echo": {"args": {"x": "segment"}, "resource": "repo:echo:{x}:{x}", "profile": "capability"}})
    law["targets"][0].update(resource="repo:echo:a:b", repair="echo")
    with raises(LawError, "F1"):
        Kernel().load(law)
    law["targets"][0]["resource"] = "repo:echo:a:a"
    Kernel().load(law)


def test_a_changed_obligation_cannot_close_an_old_contract():
    from test_language import world, workitem
    w, ci_grant, t = world(workitem("refuse"))
    w.add("signal", "ci", t, under=ci_grant, resource="repo:pr:42", key="wi-1")
    changed = copy.deepcopy(w.law)
    changed["obligations"][0]["close"][0]["where"]["result"] = "fail"
    _, t = w.widen("law", t + 1, release=changed)
    w.refuse("OBL.CONTRACT", "verdict", "ci", t, under=ci_grant,
             resource="repo:pr:42", workitem="wi-1", result="fail")
    assert "workitem:wi-1" in w.state["obligations"]
    _, t = w.widen("law", t + 1, release=w.law)
    w.add("verdict", "ci", t, under=ci_grant, resource="repo:pr:42", workitem="wi-1", result="pass")
    assert "workitem:wi-1" not in w.state["obligations"]


def test_old_closures_do_not_earn_rights_under_a_changed_obligation():
    from test_language import world, workitem
    w, ci_grant, t = world(workitem("refuse"), conditions={"earned": {"all": [{"closed_at_least": ["workitem", 1]}]}})
    gid, t = w.grant("agent", ["effect:merge"], ["repo:pr:*"], t, conditions=["earned"])
    w.add("signal", "ci", t, under=ci_grant, resource="repo:pr:42", key="wi-1")
    w.add("verdict", "ci", t + 1, under=ci_grant, resource="repo:pr:42", workitem="wi-1", result="pass")
    changed = copy.deepcopy(w.law)
    changed["obligations"][0]["due_ms"] //= 2
    _, t = w.widen("law", t + 2, release=changed)
    w.refuse("LAW.CONDITION", "intent", "agent", t, under=gid, op="merge", args=ARGS)


def test_an_obligation_contract_fault_in_the_kernel_halts():
    from test_language import world, workitem
    w, ci_grant, t = world(workitem("refuse"))
    original = w.kernel._law_obligations
    def buggy(state, record, delta):
        original(state, record, delta)
        for op in delta:
            if op[:2] == ("put", "obligations"):
                op[3]["stage"] = "forged-stage"
                op[3]["contract"] = None
    w.kernel._law_obligations = buggy
    w.refuse("HALT.DISAGREEMENT", "signal", "ci", t, under=ci_grant, resource="repo:pr:42", key="wi-1")
    assert w.pins.halted()


if __name__ == "__main__":
    run(globals())
