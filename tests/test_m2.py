"""M2 floors: an agent repairs a technical target by merging one exact commit, authorized only by facts observed on
that commit by an independent scanner; organisational targets are attested by a human and never repaired by an op."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixture import DAY, T0, World, raises, run  # noqa: E402
from test_accountability import health  # noqa: E402
from tcb.floors import FLOORS  # noqa: E402
from tcb.law import LawError, _ops, _reaches  # noqa: E402

HEAD = "a" * 40
ARGS = {"area": "deps", "item": "vulns", "pr": "7", "head": HEAD, "method": "squash"}
AT = f"repo:deps:vulns/pr/7/{HEAD}"


def setup(condition="remediate-autonomous"):
    w = World()
    gid, t = w.grant("agent", ["effect:remediate"], ["repo:deps:*", "repo:code:*"], T0 + 1, conditions=[condition])
    scan, t = w.grant("ci", ["observe", "certify:real"], ["repo:*"], t)
    return w, gid, scan, t


def test_every_technical_floor_is_repairable_by_a_commit_under_it():
    ops = _ops(FLOORS["ops"])
    for t in FLOORS["targets"]:
        if t.get("repair") == "remediate":
            assert _reaches(ops["remediate"], t["resource"]), t["id"]
    assert not _reaches(ops["remediate"], "repo:deps:vulns:extra")          # a child only below '/'
    assert all(t.get("human") is True for t in FLOORS["targets"] if t["resource"].startswith("org:"))


def test_merge_needs_green_dependency_scope_on_the_exact_commit():
    w, gid, scan, t = setup()
    w.refuse("LAW.CONDITION", "intent", "agent", t, under=gid, op="remediate", args=ARGS)
    w.add("observation", "ci", t + 1, under=scan, resource=AT, property="ci", status="green", level="real")
    w.refuse("LAW.CONDITION", "intent", "agent", t + 2, under=gid, op="remediate", args=ARGS)
    w.add("observation", "ci", t + 3, under=scan, resource=AT, property="scope", status="dependencies", level="real")
    w.add("intent", "agent", t + 4, under=gid, op="remediate", args=ARGS)
    other = dict(ARGS, head="b" * 40)                                     # facts of one commit never cover another
    w.refuse("LAW.CONDITION", "intent", "agent", t + 5, under=gid, op="remediate", args=other)


def test_code_changes_need_an_independent_review():
    w, gid, scan, t = setup("remediate-reviewed")
    for i, (prop, status) in enumerate((("ci", "green"), ("scope", "dependencies"))):
        w.add("observation", "ci", t + i, under=scan, resource=AT, property=prop, status=status, level="real")
    t += 2
    w.refuse("LAW.CONDITION", "intent", "agent", t + 1, under=gid, op="remediate", args=ARGS)
    w.add("observation", "ci", t + 2, under=scan, resource=AT, property="review", status="approved", level="real")
    w.add("intent", "agent", t + 3, under=gid, op="remediate", args=ARGS)


def test_the_agent_cannot_observe_its_own_commit():
    w, gid, scan, t = setup()
    own, t = w.grant("agent", ["observe", "certify:real"], ["repo:*"], t)
    for i, (prop, status) in enumerate((("ci", "green"), ("scope", "dependencies"))):
        w.add("observation", "agent", t + i, under=own, resource=AT, property=prop, status=status, level="real")
    t += 2
    w.refuse("LAW.CONDITION", "intent", "agent", t + 1, under=gid, op="remediate", args=ARGS)


def test_an_attestation_closes_an_organisational_gap_only_from_the_officer():
    w = World()
    mine, t = w.grant("alice", ["observe", "certify:real"], ["org:*"], T0 + 1)
    w.add("observation", "alice", t, under=mine, resource="org:isms:policy", property="attested", status="current",
          level="real")
    proven = lambda: {p["target"] for p in health(w)["proven"]}
    assert "isms" not in proven()                                          # the owner is not the declared source
    officer, t = w.grant("carol", ["observe", "certify:real"], ["org:*"], t + 1)
    for i, res in enumerate(("org:controls:soa", "org:isms:policy")):
        w.add("observation", "carol", t + i, under=officer, resource=res, property="attested" if "isms" in res
              else "coverage", status="current" if "isms" in res else "complete", level="real")
    assert {"soa", "isms"} <= proven()


def test_a_client_cannot_give_an_organisational_target_an_automatic_repair():
    from tcb.law import compose
    from fixture import make_law
    law = make_law(targets=[{"id": "x", "kind": "property", "coverage": "soa", "resource": "org:isms:other",
                             "property": "attested", "expect": "current", "min_level": "real", "fresh_ms": DAY,
                             "due_ms": DAY, "owner": "alice", "sources": ["carol"], "repair": "remediate"}])
    with raises(LawError, "F1"):
        compose(law)


if __name__ == "__main__":
    run(globals())
