"""Shared harness: the e2e cycle of tests/test_ops.py with GitHub faked, run against the nosec copy."""
import contextlib
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from ops import cycle, node as node_mod, scan
from ops.node import KINDS, Node, load_keys, new_keys, public

GOOD = {"vulns": "none", "deps-age": "none", "licenses": "compliant", "secrets": "none", "sast": "none",
        "actions": "all", "sbom": "current", "ci": "green", "branch": "pr-and-checks"}


class Clock:
    def __init__(self):
        self.t = 1_800_000_000.0

    def __call__(self):
        return self.t


class Resp:
    def __init__(self, status, body):
        self.status, self.body = status, body

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self):
        return json.dumps(self.body).encode()


def args(state, **kw):
    base = dict(state=state, keys=None, publics=None, days=90, repo="o/demo", checkout=".", agent_login="standard-agent[bot]",
                health=None, resource=None, out=None)
    return SimpleNamespace(**{**base, **kw})


def make_keys(tmp, name="keys"):
    keys = new_keys(KINDS)
    path = Path(tmp) / f"{name}.json"
    path.write_text(json.dumps(keys))
    loaded = load_keys(str(path))
    publics = Path(tmp) / f"{name}-publics.json"
    publics.write_text(json.dumps({n: public(k) for n, k in loaded.items()}))
    return loaded, str(publics)


class World:
    """gh: object with pulls/pull/files/reviews/check_runs; merge_status: what PUT /merge returns."""

    def __init__(self, gh, measured=None):
        self.tmp = tempfile.mkdtemp()
        self.keys, self.publics = make_keys(self.tmp)
        self.state = str(Path(self.tmp) / "state")
        self.clock, self.gh, self.calls = Clock(), gh, []
        self.measured = dict(measured or GOOD)
        self.merge_status = 200

    def opener(self, req, timeout):
        self.calls.append((req.get_method(), req.full_url, json.loads(req.data) if req.data else None))
        pr = req.full_url.split("/pulls/")[1].split("/")[0]
        if req.get_method() == "GET":
            return Resp(200, self.gh.pull(pr))
        if self.merge_status == 200:
            self.gh.merge(pr)
            return Resp(200, {"merged": True})
        import urllib.error
        raise urllib.error.HTTPError(req.full_url, self.merge_status, "x", {}, None)

    @contextlib.contextmanager
    def env(self):
        with patch.object(node_mod.time, "time", self.clock), patch.object(cycle.time, "time", self.clock), \
                patch.dict("os.environ", {"GITHUB_TOKEN": "x", "AGENT_GITHUB_TOKEN": "y", "MERGE_TOKEN": "z"}), \
                patch("ops.gh.Client", lambda repo, token: self.gh), \
                patch.object(scan, "measure", lambda repo, g: dict(self.measured)), \
                patch("adapters.github.urllib.request.urlopen", self.opener):
            yield

    def step(self, command, keys=None, state=None, **kw):
        state = state or self.state
        gfile = Path(state) / "genesis.json"
        expected = getattr(self, "pin", None) or (json.loads(gfile.read_text())["pin"] if gfile.exists() else None)
        n = Node(state, keys or self.keys, create=command == "init", expected_genesis=expected)
        try:
            getattr(cycle, "cmd_" + command)(n, args(state, publics=self.publics, **kw))
            return n.state
        finally:
            n.close()

    def boot(self):
        self.step("init")
        self.pin = getattr(self, "pin", None) or json.loads((Path(self.state) / "genesis.json").read_text())["pin"]
        self.clock.t += 3_700
        self.step("activate")
