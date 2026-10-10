"""End to end on a simulated world over a real git repository: a vulnerable lock is measured, the agent builds the
recipe's commit, the scanner recomputes it from the base, the law admits the fast-forward, the guard moves main to
exactly that commit, the scanner proves it, and the dossier rebuilds from the journal."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixture import run  # noqa: E402
from sim import Sim  # noqa: E402
from compliance.dossier import build, rows_of, verify  # noqa: E402
from ops.node import load_keys  # noqa: E402


def test_a_vulnerable_lock_is_repaired_by_its_recipe_and_proven():
    with Sim({"vulns": "found:2"}) as sim:
        before = sim.world.main_head()
        sim.cycle()                                         # measure; the agent builds and declares the recipe
        (resource, phase), = sim.subjects().items()
        assert phase == "measuring" and resource.startswith(f"repo:deps:vulns/{before}/")
        head = resource.rsplit("/", 1)[1]
        s = sim.cycle(minutes=60)                           # reproduced + green: asked, fast-forwarded
        assert sim.world.main_head() == head and list(s["executed"].values()) == ["ok"]
        assert sim.world.blob(sim.world.tree(head)["requirements.txt"]) == b"flask==2.2.5\nrequests==2.31.0\n"
        sim.measured["vulns"] = "none"
        s = sim.cycle(minutes=60)
        assert sim.subjects()[resource] == "proven" and not any(k.startswith("proof:") for k in s["obligations"])
        assert len(s["executed"]) == 1
        n = sim.node()
        try:
            rows = rows_of(n.journal.path)
            d = build(rows, genesis_pin=sim.genesis, checkpoints=n.pins.load(), required_at=int(sim.clock.t * 1000))
            assert d["measures"]["vulns"]["status"] == "PROUVÉ"
            assert verify(d, rows, genesis_pin=sim.genesis, checkpoints=n.pins.load())
        finally:
            n.close()


def test_the_adapter_fast_forwards_only_from_the_judged_base():
    from adapters.github import GitHub
    B, H, X = "b" * 40, "c" * 40, "d" * 40

    def attempt(main, graphql_ok=True):
        sent = []

        def reply(body):
            return type("R", (), {"status": 200, "read": lambda self: body, "__enter__": lambda self: self,
                                  "__exit__": lambda self, *a: False})()

        def opener(req, timeout):
            sent.append((req.get_method(), json.loads(req.data) if req.data else None))
            if req.get_method() == "GET":
                return reply(json.dumps({"node_id": "REPO"} if req.full_url.endswith("/demo")
                                        else {"object": {"sha": main}}).encode())
            return reply(b'{"data":{"updateRefs":{"clientMutationId":"k"}}}' if graphql_ok
                         else b'{"errors":[{"message":"conflict"}]}')
        result = GitHub("o/demo", "t", opener=opener).remediate("r", {"area": "deps", "item": "vulns", "base": B,
                                                                      "head": H}, "k")
        return result, sent
    result, sent = attempt(B)
    assert result == "ok" and [method for method, _ in sent] == ["GET", "GET", "POST"]
    assert sent[-1][1]["variables"]["input"]["refUpdates"] == [
        {"name": "refs/heads/main", "beforeOid": B, "afterOid": H, "force": False}]
    assert attempt(H) == ("ok", [("GET", None)])                       # already there: nothing sent
    assert attempt(X) == ("failed", [("GET", None)])                   # main moved: the judged transition is gone
    assert attempt(B, False)[0] == "unknown"


def test_demo_report_exposes_current_law_and_unverified_t_without_a_grant():
    import tempfile
    from types import SimpleNamespace
    from ops.cycle import cmd_report
    with Sim() as sim, tempfile.TemporaryDirectory() as tmp:
        n = sim.node()
        try:
            cmd_report(n, SimpleNamespace(out=tmp))
            surface = (Path(tmp) / "constitution.md").read_text()
            assert n.state["head"] in surface
            assert n.state["law"]["digest"] in surface
            assert "vulns" in surface and "T06" in surface
            assert "Lecture seule" in surface and "allowed" not in surface
        finally:
            n.close()


def test_demo_scanner_rejects_measurement_under_another_law():
    with Sim() as sim:
        sim.run("witness")
        sim.run("measure")
        sim.run("test")
        before = sim.node()
        try:
            head = before.state["head"]
        finally:
            before.close()
        path = sim.tmp / "measured.json"
        measured = json.loads(path.read_text())
        measured["law_digest"] = "sha256:" + "0" * 64
        path.write_text(json.dumps(measured))
        try:
            sim.run("scan")
        except ValueError as exc:
            assert "another constitutional law" in str(exc)
        else:
            raise AssertionError("the scanner accepted observations under another law")
        after = sim.node()
        try:
            assert after.state["head"] == head
        finally:
            after.close()


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
