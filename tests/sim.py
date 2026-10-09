"""A simulated world for the untrusted roles: GitHub as typed answers, a controlled clock, keys, and a driver that
runs the roles of ops.cycle in order against one state directory."""
import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ops import cycle, node as node_mod  # noqa: E402
from ops.node import KINDS, Node, load_keys, new_keys, public  # noqa: E402
from tcb import EffectPort  # noqa: E402

HEAD = "c" * 40
MAIN = "a" * 40
GOOD = {"vulns": "none", "deps-age": "none", "licenses": "compliant", "secrets": "none", "sast": "none",
        "actions": "all", "sbom": "current", "ci": "green", "branch": "pr-and-checks"}


class Clock:
    def __init__(self):
        self.t = 1_800_000_000.0

    def __call__(self):
        return self.t


class World:
    """GitHub, answering only questions about named subjects. `asked` records every subject it was asked about."""
    repo = "o/demo"

    def __init__(self):
        self.pulls = {}                       # number -> {head, base, merged, open, same_repo, files}
        self.runs = {}                        # sha -> conclusion
        self.asked = []
        self.proposals = 0

    def main_head(self):
        return MAIN

    def ci(self, sha):
        self.asked.append(("ci", sha))
        return self.runs.get(sha)

    def pull(self, number):
        self.asked.append(("pull", number))
        p = self.pulls[number]
        return {"head": p["head"], "base": p["base"], "merged": p["merged"], "open": p["open"],
                "same_repo": p["same_repo"], "changed": len(p["files"])}

    def files(self, number):
        return list(self.pulls[number]["files"])

    def rule_types(self, branch="main"):
        return {"pull_request", "required_status_checks"}

    def propose(self, branch, files, title, body):
        self.proposals += 1
        number = str(6 + self.proposals)
        self.pulls[number] = {"head": HEAD, "base": "main", "merged": False, "open": True, "same_repo": True,
                              "files": sorted(files)}
        return {"number": number, "head": HEAD}

    def merge(self, resource, args, key):
        p = self.pulls[args["pr"]]
        if p["head"] != args["head"] or p["base"] != "main":
            return "failed"
        p["merged"], p["open"] = True, False
        return "ok"


def craft(repo, target, status, key):
    return {"title": f"fix {target}", "body": "", "files": {"requirements.txt": "flask==9.9.9\n"}}


class Sim:
    def __init__(self, measured=None):
        self.tmp = Path(tempfile.mkdtemp())
        keys = new_keys(KINDS)
        (self.tmp / "keys.json").write_text(json.dumps(keys))
        self.keys = load_keys(str(self.tmp / "keys.json"))
        (self.tmp / "publics.json").write_text(json.dumps({n: public(k) for n, k in self.keys.items()}))
        self.state = str(self.tmp / "state")
        self.clock, self.world = Clock(), World()
        self.measured = dict(GOOD, **(measured or {}))
        self.merge = self.world.merge
        self._patches = [patch.object(node_mod.time, "time", self.clock), patch.object(cycle.time, "time", self.clock),
                         patch("ops.probes.measure_all", lambda repo, world, targets: dict(self.measured))]

    def __enter__(self):
        for p in self._patches:
            p.start()
        self.run("init")
        self.clock.t += 3_700
        self.run("activate")
        return self

    def __exit__(self, *exc):
        for p in self._patches:
            p.stop()
        return False

    @property
    def genesis(self):
        return json.loads(Path(self.state, "genesis.json").read_text())["pin"]

    def node(self, create=False):
        return Node(self.state, self.keys, create=create, expected_genesis=None if create else self.genesis)

    def run(self, command, **kw):
        n = self.node(create=command == "init")
        a = SimpleNamespace(**{**dict(state=self.state, publics=str(self.tmp / "publics.json"), days=90, repo="o/demo",
                                      checkout=".", pr=None, reviewer="icham", resource=None, out=None), **kw})
        try:
            fn = getattr(cycle, "cmd_" + command)
            if command == "scan":
                fn(n, a, world=self.world)
            elif command == "agent":
                fn(n, a, world=self.world, craft=craft)
            elif command == "guard":
                fn(n, a, port=EffectPort({"remediate": lambda r, args, k: self.merge(r, args, k)}))
            else:
                fn(n, a)
            return n.state
        finally:
            n.close()

    def cycle(self, minutes=1):
        self.clock.t += minutes * 60
        self.run("scan")
        self.run("agent")
        return self.run("guard")
