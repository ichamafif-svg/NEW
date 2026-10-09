"""End to end on a simulated world: a vulnerable dependency is measured, a repair commit is crafted and declared,
the scanner observes that exact commit, the law admits its merge, the guard merges it once, the scanner proves it,
and the dossier rebuilds from the journal."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixture import run  # noqa: E402
from sim import HEAD, Sim  # noqa: E402
from compliance.dossier import build, rows_of, verify  # noqa: E402
from ops.node import load_keys  # noqa: E402


def test_a_vulnerability_is_repaired_under_the_law_and_proven():
    with Sim({"vulns": "found:3"}) as sim:
        s = sim.cycle()                                      # measure, craft + declare, nothing to merge yet
        assert sim.world.proposals == 1 and not s["intents"]
        s = sim.cycle()                                      # observe the declared commit (CI pending): no ask
        assert not s["intents"]
        sim.world.runs[HEAD] = "success"
        s = sim.cycle(minutes=400)                           # green, dependency scope: asked, merged
        iid = next(iter(s["intents"]))
        assert list(s["executed"].values()) == ["ok"] and sim.world.pulls["7"]["merged"]
        assert f"proof:{iid}" in s["obligations"] and sim.world.proposals == 1
        sim.measured["vulns"] = "none"
        s = sim.cycle()                                      # read back: proven; main measured clean
        assert f"proof:{iid}" not in s["obligations"]
        assert s["observations"]["repo:deps:vulns|high|scanner"]["status"] == "none"
        assert len(s["executed"]) == 1 and sim.world.proposals == 1   # nothing merged twice, nothing re-proposed
        n = sim.node()
        try:
            rows = rows_of(n.journal.path)
            d = build(rows, genesis_pin=sim.genesis, checkpoints=n.pins.load(), required_at=int(sim.clock.t * 1000))
            assert d["measures"]["vulns"]["status"] == "PROUVÉ"
            assert verify(d, rows, genesis_pin=sim.genesis, checkpoints=n.pins.load())
        finally:
            n.close()


def test_the_adapter_merges_only_the_judged_commit_and_reports_honestly():
    import urllib.error
    from adapters.github import GitHub
    args = {"area": "deps", "item": "vulns", "pr": "7", "head": HEAD, "method": "squash"}

    def with_put(status, merged=False, base="main"):
        sent = []

        def reply(body):
            return type("R", (), {"status": 200, "read": lambda self: body, "__enter__": lambda self: self,
                                  "__exit__": lambda self, *a: False})()

        def opener(req, timeout):
            sent.append(req.get_method())
            if req.get_method() == "GET":
                return reply(json.dumps({"merged": merged, "head": {"sha": HEAD}, "base": {"ref": base}}).encode())
            if status == 200:
                return reply(b"{}")
            raise urllib.error.HTTPError(req.full_url, status, "x", {}, None)
        return GitHub("o/demo", "t", opener=opener).remediate("r", dict(args), "k"), sent
    assert with_put(200) == ("ok", ["GET", "PUT"])
    assert with_put(409) == ("failed", ["GET", "PUT"])                 # head moved: GitHub merged nothing
    assert with_put(502) == ("unknown", ["GET", "PUT"])                # may have merged: reconcile
    assert with_put(200, merged=True) == ("ok", ["GET"])               # already landed: no second send
    assert with_put(200, base="standard-journal") == ("failed", ["GET"])
    assert GitHub("o/demo", "t", opener=None).remediate("r", dict(args, head="HEAD"), "k") == "failed"


def test_unknown_identities_in_key_material_are_refused():
    import tempfile
    p = Path(tempfile.mkdtemp()) / "k.json"
    p.write_text(json.dumps({"mallory": "AAAA"}))
    try:
        load_keys(str(p))
    except ValueError:
        return
    raise AssertionError("unknown identity accepted")


if __name__ == "__main__":
    run(globals())
