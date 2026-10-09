"""The rules of the ops layer (docs/M2.md), stated as properties. The attacks of review rounds 1 and 2 are instances."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixture import raises, run  # noqa: E402
from sim import Sim  # noqa: E402
from ops import agent, lifecycle, probes  # noqa: E402
from ops.node import Node  # noqa: E402


def test_rule1_commits_nobody_declared_are_never_asked_about():
    with Sim({"vulns": "found:2"}) as sim:
        rogue = sim.world.commit(sim.world.main_head(), {"requirements.txt": b"evil==1\n"}, "rogue")
        sim.world.keep(rogue)
        for _ in range(3):
            sim.cycle(minutes=60)
        assert all(rogue not in c for c in sim.world.calls) and sim.world.main_head() != rogue


def test_rule1_a_review_names_the_head_a_human_read():
    with Sim({"sast": "found:1"}) as sim:
        sim.cycle()
        sim.cycle()
        (resource, phase), = sim.subjects().items()
        assert phase == "awaiting-review"                      # a model's change has no recipe: no autonomy
        with raises(SystemExit, "not the head"):
            sim.run("review", head="f" * 40)
        sim.run("review", head=resource.rsplit("/", 1)[1])
        sim.cycle()
        assert sim.world.main_head() == resource.rsplit("/", 1)[1]


def test_rule2_only_full_coverage_without_findings_passes():
    M = probes.Measure
    assert probes.verdict("none", M(frozenset("ab"), frozenset("ab"))) == "none"
    assert probes.verdict("none", M(frozenset("ab"), frozenset("a"))) == "uncovered:1"
    assert probes.verdict("none", M(frozenset(), frozenset())) == "uncovered:empty"
    assert probes.verdict("none", RuntimeError()) == "uncovered:RuntimeError"
    assert probes.verdict("none", M(frozenset("a"), frozenset("a"), ("x",))) == "found:1"


def test_rule3_hostile_data_stays_inside_its_scope_and_state_needs_the_pin():
    for path in (".git/config", "../x.py", "/etc/passwd", ".github/workflows/standard.yml", "tests/t.py",
                 "requirements.txt"):
        assert not agent.in_scope("sast", path), path
    with Sim() as sim:
        with raises(ValueError, "externally pinned genesis"):
            Node(sim.state, sim.keys, expected_genesis="sha256:" + "1" * 64)


def test_rule4_every_phase_has_one_next_step():
    assert lifecycle.LINE_STATES <= set(lifecycle.NEXT)


def test_rule5_a_recipe_commit_with_anything_more_is_not_reproduced():
    with Sim({"vulns": "found:2"}) as sim:
        base = sim.world.main_head()
        head = sim.world.commit(base, {"requirements.txt": b"flask==2.2.5\nrequests==2.31.0\n",
                                       "app/backdoor.py": b"import os\n"}, "recipe plus more")
        n = sim.node()
        try:
            from ops.cycle import observe
            observe(n, "agent", f"repo:deps:vulns/{base}/{head}", "proposed", "open", level="unknown", force=True)
        finally:
            n.close()
        sim.cycle()
        assert sim.world.main_head() == base
        assert sim.subjects()[f"repo:deps:vulns/{base}/{head}"] == "awaiting-review"


def test_rule6_red_tests_withdraw_and_free_the_target():
    with Sim({"vulns": "found:2"}) as sim:
        sim.default_test = "found:1"
        sim.cycle()
        sim.cycle()
        phases = sim.subjects()
        assert list(phases.values()).count("withdrawn") == 1 and sim.world.main_head() not in str(phases)


if __name__ == "__main__":
    run(globals())
