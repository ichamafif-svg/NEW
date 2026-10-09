"""End to end, with GitHub and Claude faked and the clock controlled: genesis, witnessed activation, a vulnerable
dependency observed, a repair pull request, the law's merge of its exact commit, read-back proof, a proven target and
a dossier that rebuilds from the journal."""
import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))
from fixture import run  # noqa: E402
from ops import cycle, node as node_mod, scan  # noqa: E402
from ops.node import KINDS, Node, load_keys, new_keys, public  # noqa: E402

HEAD = "c" * 40


class Clock:
    def __init__(self):
        self.t = 1_800_000_000.0

    def __call__(self):
        return self.t


class FakeGH:
    def __init__(self):
        self.merged = False
        self.pr_open = False

    def pulls(self):
        return [{"number": 7, "head": {"ref": "standard/deps/vulns/abcd1234", "sha": HEAD}}] if self.pr_open else []

    def pull(self, n):
        return {"merged": self.merged, "head": {"sha": HEAD}}


def opener_for(gh, calls):
    class Resp:
        def __init__(self, status, body):
            self.status, self.body = status, body

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return json.dumps(self.body).encode()

    def opener(req, timeout):
        calls.append((req.get_method(), req.full_url, json.loads(req.data) if req.data else None))
        if req.get_method() == "GET":
            return Resp(200, {"merged": gh.merged, "head": {"sha": HEAD}})
        gh.merged = True
        return Resp(200, {"merged": True})
    return opener


def setup(tmp):
    keys = new_keys(KINDS)
    path = Path(tmp) / "keys.json"
    path.write_text(json.dumps(keys))
    loaded = load_keys(str(path))
    publics = Path(tmp) / "publics.json"
    publics.write_text(json.dumps({n: public(k) for n, k in loaded.items()}))
    return str(path), str(publics)


def args(state, **kw):
    base = dict(state=state, keys=None, publics=None, days=90, repo="o/demo", checkout=".", agent_login="bot",
                health=None, resource=None, out=None)
    return SimpleNamespace(**{**base, **kw})


def test_a_vulnerability_is_repaired_under_the_law_and_proven():
    tmp = tempfile.mkdtemp()
    keyfile, publics = setup(tmp)
    state = str(Path(tmp) / "state")
    clock, gh, calls = Clock(), FakeGH(), []
    good = {"vulns": "none", "deps-age": "none", "licenses": "compliant", "secrets": "none", "sast": "none",
            "actions": "all", "sbom": "current", "ci": "green", "branch": "pr-and-checks"}
    measured = dict(good, vulns="found:1")
    facts = []
    keys = load_keys(keyfile)

    def step(command, **kw):
        pinned = Path(state, "genesis.json")
        expected = json.loads(pinned.read_text())["pin"] if pinned.exists() else None
        n = Node(state, keys, create=command == "init", expected_genesis=expected)
        try:
            getattr(cycle, "cmd_" + command)(n, args(state, publics=publics, **kw))
            return n.state
        finally:
            n.close()

    with patch.object(node_mod.time, "time", clock), patch.object(cycle.time, "time", clock), \
            patch.dict("os.environ", {"GITHUB_TOKEN": "x", "AGENT_GITHUB_TOKEN": "y", "MERGE_TOKEN": "z"}), \
            patch("ops.gh.Client", lambda repo, token: gh), \
            patch.object(scan, "measure", lambda repo, g: dict(measured)), \
            patch.object(scan, "pull_facts", lambda g, login: list(facts)), \
            patch("ops.agent.open_repair", lambda *a: (setattr(gh, "pr_open", True), {"number": 7})[1]), \
            patch("adapters.github.urllib.request.urlopen", opener_for(gh, calls)):
        step("init")
        clock.t += 3_700
        step("activate")
        s = step("scan")
        assert s["observations"]["repo:deps:vulns|high|scanner"]["status"] == "found:1"
        health = {"open": [{"type": "target", "target": "vulns", "due": 1, "needs": ["repair"]}], "escalated": []}
        hpath = Path(tmp) / "health.json"
        hpath.write_text(json.dumps(health))
        step("repair", health=str(hpath))
        assert gh.pr_open
        resource = f"repo:deps:vulns/pr/7/{HEAD}"
        facts[:] = [(resource, "ci", "green"), (resource, "scope", "code")]
        clock.t += 60
        step("scan")
        s = step("ask")
        assert not s["intents"], "code scope without review must not be asked"
        facts.append((resource, "scope", "dependencies"))
        clock.t += 60
        step("scan")
        s = step("ask")
        iid = next(iter(s["intents"]))
        s = step("guard")
        assert s["executed"] and list(s["executed"].values()) == ["ok"]
        assert [c[0] for c in calls] == ["GET", "PUT"] and calls[1][2]["sha"] == HEAD
        assert f"proof:{iid}" in s["obligations"]
        step("guard")                                                  # a rerun sends nothing
        assert len(calls) == 2
        measured.update(good)
        clock.t += 60
        s = step("scan")
        assert f"proof:{iid}" not in s["obligations"], "the read-back closes the proof"
        assert s["observations"]["repo:deps:vulns|high|scanner"]["status"] == "none"
        genesis = json.loads(Path(state, "genesis.json").read_text())["pin"]
        n = Node(state, keys, expected_genesis=genesis)
        try:
            from compliance.dossier import build, rows_of, verify
            d = build(rows_of(n.journal.path), genesis_pin=n.genesis, checkpoints=n.pins.load(),
                      required_at=int(clock.t * 1000))
            assert d["measures"]["vulns"]["status"] == "PROUVÉ"
            assert verify(d, rows_of(n.journal.path), genesis_pin=genesis, checkpoints=n.pins.load())
        finally:
            n.close()


def test_the_adapter_merges_only_the_judged_commit_and_reports_honestly():
    import urllib.error
    from adapters.github import GitHub
    args = {"area": "deps", "item": "vulns", "pr": "7", "head": HEAD, "method": "squash"}

    def with_put(status, merged=False):
        sent = []

        def opener(req, timeout):
            sent.append(req.get_method())
            if req.get_method() == "GET":
                body = json.dumps({"merged": merged, "head": {"sha": HEAD}}).encode()
                return type("R", (), {"status": 200, "read": lambda self: body, "__enter__": lambda self: self,
                                      "__exit__": lambda self, *a: False})()
            if status == 200:
                return type("R", (), {"status": 200, "read": lambda self: b"{}", "__enter__": lambda self: self,
                                      "__exit__": lambda self, *a: False})()
            raise urllib.error.HTTPError(req.full_url, status, "x", {}, None)
        return GitHub("o/demo", "t", opener=opener).remediate("r", dict(args), "k"), sent
    assert with_put(200) == ("ok", ["GET", "PUT"])
    assert with_put(409) == ("failed", ["GET", "PUT"])                 # head moved: GitHub merged nothing
    assert with_put(502) == ("unknown", ["GET", "PUT"])                # may have merged: reconcile
    assert with_put(200, merged=True) == ("ok", ["GET"])               # already landed: no second send
    assert GitHub("o/demo", "t", opener=None).remediate("r", dict(args, head="HEAD"), "k") == "failed"


def test_unknown_identities_in_key_material_are_refused():
    tmp = tempfile.mkdtemp()
    p = Path(tmp) / "k.json"
    p.write_text(json.dumps({"mallory": "AAAA"}))
    try:
        load_keys(str(p))
    except ValueError:
        return
    raise AssertionError("unknown identity accepted")


if __name__ == "__main__":
    run(globals())
