"""The budget split rests on structure, checked here: the second judge is joined by AND (it can only stop what the
kernel admitted), and accountability has no path to admission or effects."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixture import T0, Refused, World, raises, run  # noqa: E402
from tcb import invariants  # noqa: E402

ARGS = {"pr": "42", "method": "squash"}


def ready(w):
    gid, t = w.grant("agent", ["effect:merge"], ["repo:pr:*"], T0 + 1)
    return gid, t


def test_a_second_judge_that_accepts_everything_admits_nothing_the_kernel_refuses():
    w = World()
    gid, t = ready(w)
    original = invariants.Invariants.check, invariants.Invariants.dispatch
    invariants.Invariants.check = lambda self, *a, **k: None
    try:
        with raises(Refused, "CAP.SCOPE"):
            w.add("observation", "agent", t, under=gid, resource="repo:pr:42", property="ci", status="green", level="real")
        w.add("revoke", "carol", t + 1, grant=gid)
        with raises(Refused, "CAP.WITHDRAWN"):
            w.add("intent", "agent", t + 2, under=gid, op="merge", args=ARGS)
    finally:
        invariants.Invariants.check, invariants.Invariants.dispatch = original


def test_a_second_judge_that_fails_halts_and_sends_nothing():
    w = World()
    gid, t = ready(w)
    iid = w.add("intent", "agent", t, under=gid, op="merge", args=ARGS)
    sent = []
    g = w.guard(lambda *a: sent.append(a) or "ok")
    g.issue(iid, t + 1)
    original = invariants.Invariants.dispatch
    invariants.Invariants.dispatch = lambda self, *a, **k: (_ for _ in ()).throw(RuntimeError("broken second judge"))
    try:
        try:
            g.redeem(w.state["token_of"][iid], t + 2)
        except Refused:
            pass
        assert sent == [], "a failing second judge must never let an effect leave"
        with raises(Refused, "HALT.DISAGREEMENT"):
            w.add("freeze", "sentinel", t + 3, scope="repo:pr:*")
    finally:
        invariants.Invariants.dispatch = original


def test_accountability_has_no_path_to_admission_or_effects():
    import ast
    root = Path(__file__).resolve().parents[1] / "tcb"
    visibility = {"accountability", "health", "worker", "sandbox"}
    for path in root.glob("*.py"):
        if path.stem in visibility | {"__init__"}:
            continue
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.ImportFrom) and node.level == 1:
                names = {node.module.split(".")[0]} if node.module else {a.name for a in node.names}
                assert not names & visibility, f"{path.stem} imports {names & visibility}"


if __name__ == "__main__":
    run(globals())
