"""Floors and client law: the release imposes the floors on every client; the client law lives in the journal, binds
the floor roles, adds and tightens, never weakens; the autonomy floor requires a repair route for every target."""
import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixture import DAY, H, T0, FLOORS, Kernel, Refused, World, digest, make_law, raises, run  # noqa: E402
from tcb import Journal  # noqa: E402
from tcb.law import LawError  # noqa: E402


def invalid(law, match):
    with raises(LawError, match):
        Kernel().load(law)


def test_floors_apply_to_every_client_without_being_asked():
    w = World()
    law = w.kernel.law_of(w.state)
    floor = next(t for t in law.release["targets"] if t["id"] == "inventory")
    assert floor["owner"] == "alice" and floor["sources"] == ["ci"]          # roles bound to the client's identities
    assert any(o["obligation"] == "target:inventory" for o in w.journal.health()["open"])
    invalid({k: v for k, v in make_law().items() if k != "bindings"}, "bindings")


def test_a_client_never_redefines_or_weakens_a_floor():
    invalid(make_law(ops={"merge": {"args": {"pr": "segment"}, "resource": "repo:pr:{pr}", "profile": "capability"}}),
            "never redefines")
    invalid(make_law(conditions={"bot-author": {"all": [{"prefix": ["resource", "repo:"]}]}}), "never redefines")
    invalid(make_law(evidence={"evidence": {"fields": {"under": "id", "resource": "resource"}}}), "never redefines")
    clash = make_law()
    clash["targets"].append({**copy.deepcopy(FLOORS["targets"][0]), "owner": "alice", "sources": ["ci"]})
    invalid(clash, "never redefines")
    invalid(make_law(delays={"grant": 60_000}), "only tighten")
    invalid(make_law(ttl={"observation": 2 * DAY}), "only tighten")
    invalid(make_law(tighten={"targets": {"inventory": {"fresh_ms": 2 * DAY}}}), "only shorten")
    invalid(make_law(tighten={"targets": {"inventory": {"min_level": "unknown"}}}), "only rise")
    invalid(make_law(floors=digest({"other": "release"})), "floors of this release")
    tightened = Kernel().load(make_law(ttl={"observation": H}, delays={"grant": 2 * H},
                                       tighten={"targets": {"inventory": {"fresh_ms": H}}}))
    assert tightened.ttl["observation"] == H and tightened.delay["grant"] == 2 * H


def test_every_target_needs_an_autonomous_repair_route_or_a_human_declaration():
    law = make_law()
    del law["targets"][0]["repair"]
    invalid(law, "F1: target pr42-ci")
    law["targets"][0]["repair"] = "inventory-refresh"                      # an op that cannot reach repo:pr:42
    invalid(law, "F1: target pr42-ci")
    law["targets"][0].pop("repair")
    law["targets"][0]["human"] = True
    Kernel().load(law)


def test_the_client_law_changes_by_widening_and_history_still_replays():
    w = World()
    gid, t = w.grant("agent", ["effect:merge"], ["repo:pr:*"], T0 + 1)
    before = w.add("intent", "agent", t, under=gid, op="merge", args={"pr": "42", "method": "squash"})
    law = copy.deepcopy(w.law)
    law["targets"].append({"id": "pr43-ci", "kind": "property", "coverage": "inventory", "resource": "repo:pr:43",
                           "property": "ci", "expect": "green", "min_level": "real", "fresh_ms": DAY,
                           "due_ms": DAY, "owner": "alice", "sources": ["ci"], "repair": "merge"})
    w.refuse("FLOOR0.QUORUM", "law", "alice", t + 1, release=law)
    w.refuse("LAW.INVALID", "law", "alice", t + 1, ["alice", "bob"], release=make_law(delays={"law": 1}))
    pid = w.add("law", "alice", t + 2, ["alice", "bob"], release=law)
    stale = w.add("law", "alice", t + 3, ["alice", "bob"], release=make_law(ttl={"proof": H}))
    w.refuse("WIDEN.DELAY", "activate", "alice", t + 4, ["alice", "bob"], proposal=pid)
    w.tick(t + 3 + H)
    w.add("activate", "alice", t + 4 + H, ["alice", "bob"], proposal=pid)
    w.refuse("WIDEN.STALE", "activate", "alice", t + 5 + H, ["alice", "bob"], proposal=stale)
    assert any(o["obligation"] == "target:pr43-ci" for o in w.journal.health()["open"])
    fresh = Journal(w.path, Kernel(code_pin=w.kernel.code_pin), genesis_pin=w.journal.genesis_pin, checkpoints=w.pins)
    assert before in fresh.snapshot()["intents"]                           # each entry re-judged under its own law


def test_invariants_catch_a_kernel_that_changes_the_law_without_activation():
    w = World()
    law = make_law(ttl={"proof": H})
    def buggy(s, b, signers, d):
        d.append(("set", "law", {"digest": w.kernel.load(b["release"]).digest, "client": b["release"]}))
    w.kernel._law = buggy
    w.refuse("HALT.DISAGREEMENT", "law", "alice", T0 + 1, ["alice", "bob"], release=law)


def test_one_departure_per_reservation():
    w = World()
    gid, t = w.grant("agent", ["effect:merge"], ["repo:pr:*"], T0 + 1)
    iid = w.add("intent", "agent", t, under=gid, op="merge", args={"pr": "42", "method": "squash"})
    calls = []
    g = w.guard(lambda *a: calls.append(a) or "ok")
    g.issue(iid, t + 1)
    tid = w.state["token_of"][iid]
    g.redeem(tid, t + 2)
    with raises(Refused, "OBL.NOT_OPEN"):
        g.redeem(tid, w.state["last_at"] + 1)
    assert len(calls) == 1


if __name__ == "__main__":
    run(globals())
