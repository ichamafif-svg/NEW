"""A simulated world for the untrusted roles, over a real local git repository: GitHub's git objects are git's own,
main is a real ref, the agent's commits are real child commits, and the guard's effect is a real fast-forward.
Only what needs the network is faked: the advisory database, PyPI, rulesets, the test runner and the model."""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ops import cycle, node as node_mod, probes  # noqa: E402
from ops.node import KINDS, Node, load_keys, new_keys, public  # noqa: E402
from tcb import EffectPort  # noqa: E402

GOOD = {"vulns": "none", "deps-age": "none", "licenses": "compliant", "secrets": "none", "sast": "none",
        "actions": "all", "sbom": "current", "branch": "guard-only", "lineage": "none"}
LOCK = "flask==2.2.2\nrequests==2.25.1\n"
FIX = {"flask": [["2.2.5", "2.3.2"]], "requests": [["2.31.0"]]}


def git(repo, *args, input=None, env=None):
    r = subprocess.run(["git", *args], cwd=repo, capture_output=True, input=input, check=True,
                       env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
                            "GIT_COMMITTER_EMAIL": "t@t", **(env or {})})
    return r.stdout


class World:
    """The ops.world.GitHub interface, answered by a local repository."""
    repo = "o/demo"

    def __init__(self, path: Path):
        self.path = path
        self.calls = []

    def _sha(self, ref):
        return git(self.path, "rev-parse", ref).decode().strip()

    def main_head(self):
        return self._sha("refs/heads/main")

    def parents(self, commit):
        self.calls.append(("parents", commit))
        return git(self.path, "rev-list", "--parents", "-n1", commit).decode().split()[1:]

    def tree(self, commit):
        self.calls.append(("tree", commit))
        out = {}
        for line in git(self.path, "ls-tree", "-r", commit).decode().splitlines():
            meta, path = line.split("\t", 1)
            out[path] = meta.split()[2]
        return out

    def blob(self, blob):
        return git(self.path, "cat-file", "blob", blob)

    def contains(self, ancestor, descendant):
        return subprocess.run(["git", "merge-base", "--is-ancestor", ancestor, descendant], cwd=self.path).returncode == 0

    def history(self, since, head, cap=10_000):
        return git(self.path, "rev-list", "--first-parent", "--reverse", f"{since}..{head}").decode().split()

    def rule_types(self, branch="main"):
        return {"update", "deletion", "non_fast_forward"}

    def tag_commit(self, owner_repo, tag):
        return hashlib.sha1(f"{owner_repo}@{tag}".encode()).hexdigest()

    def commit(self, base, files, message):
        index = self.path / ".git" / "sim-index"
        env = {"GIT_INDEX_FILE": str(index)}
        git(self.path, "read-tree", base, env=env)
        for p, data in files.items():
            blob = git(self.path, "hash-object", "-w", "--stdin", input=data).decode().strip()
            git(self.path, "update-index", "--add", "--cacheinfo", f"100644,{blob},{p}", env=env)
        tree = git(self.path, "write-tree", env=env).decode().strip()
        index.unlink()
        return git(self.path, "commit-tree", tree, "-p", base, "-m", message).decode().strip()

    def keep(self, head):
        git(self.path, "update-ref", f"refs/standard/proposals/{head}", head)

    # the guard's effect, with the adapter's semantics: fast-forward from the judged base only
    def fast_forward(self, resource, args, key):
        main = self.main_head()
        if main == args["head"]:
            return "ok"
        if main != args["base"] or not self.contains(main, args["head"]):
            return "failed"
        git(self.path, "update-ref", "refs/heads/main", args["head"], main)
        git(self.path, "reset", "-q", "--hard", "main")
        return "ok"

    def push(self, files: dict, message="outside the law"):
        """Someone changes main without the law (a test of lineage)."""
        head = self.commit(self.main_head(), {p: c.encode() for p, c in files.items()}, message)
        git(self.path, "update-ref", "refs/heads/main", head)
        git(self.path, "reset", "-q", "--hard", "main")
        return head


class Clock:
    def __init__(self):
        self.t = 1_800_000_000.0

    def __call__(self):
        return self.t


class Sim:
    """One state directory, one repository, every role in order. `measured` fakes the probes on main, `advisories`
    the vulnerability database, `tests` the test runner (resource or "main" -> status)."""

    def __init__(self, measured=None):
        self.tmp = Path(tempfile.mkdtemp())
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "-q", "-b", "main")
        for p, c in {"requirements.txt": LOCK, "app/service.py": "x = 1\n", "tests/test_x.py": "def test(): pass\n",
                     ".github/workflows/ci.yml": "jobs:\n  t:\n    steps:\n      - uses: actions/checkout@v4\n"}.items():
            (self.repo / p).parent.mkdir(parents=True, exist_ok=True)
            (self.repo / p).write_text(c)
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "init")
        self.world = World(self.repo)
        keys = new_keys(KINDS)
        (self.tmp / "keys.json").write_text(json.dumps(keys))
        self.keys = load_keys(str(self.tmp / "keys.json"))
        (self.tmp / "publics.json").write_text(json.dumps({n: public(k) for n, k in self.keys.items()}))
        self.state = str(self.tmp / "state")
        self.clock = Clock()
        self.measured = dict(GOOD, **(measured or {}))
        self.advisories = dict(FIX)
        self.tests = {"main": "green"}
        self.default_test = "green"
        self.effect = self.world.fast_forward
        self.crafted = {"app/service.py": "x = 2\n"}
        audit = lambda tree: [{"name": n, "version": "0", "vulns": [{"id": f"V-{n}", "fix_versions": f}
                                                                    for f in fixes]}
                              for n, fixes in self.advisories.items()]
        self._patches = [patch.object(node_mod.time, "time", self.clock), patch.object(cycle.time, "time", self.clock),
                         patch.object(probes, "measure_all", lambda tree, ctx, targets: dict(self.measured)),
                         patch.object(probes, "audit", audit)]

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
                                      checkout=str(self.repo), head=None, reviewer="icham", resource=None, out=None,
                                      measured=str(self.tmp / "measured.json"), tested=str(self.tmp / "tested.json")),
                               **kw})
        try:
            fn = getattr(cycle, "cmd_" + command)
            if command in ("measure", "scan", "agent"):
                extra = {"craft": lambda repo, t, st, k: {"files": dict(self.crafted)}} if command == "agent" else {}
                fn(n, a, world=self.world, **extra)
            elif command == "test":
                fn(n, a, run=lambda main, heads: {"main": self.tests["main"], "subjects": {
                    r: self.tests.get(r, self.default_test) for r in heads}},
                   fetch=lambda checkout, subjects, where: {x.resource: "." for x in subjects})
            elif command == "guard":
                fn(n, a, port=EffectPort({"remediate": lambda r, args, k: self.effect(r, args, k)}))
            else:
                fn(n, a)
            return n.state
        finally:
            n.close()

    def cycle(self, minutes=1):
        """One scheduled run: every role in the workflow's order."""
        self.clock.t += minutes * 60
        for command in ("witness", "measure", "test", "scan", "witness", "agent", "witness", "guard"):
            s = self.run(command)
        return s

    def subjects(self):
        from ops import lifecycle
        n = self.node()
        try:
            return {x.resource: lifecycle.phase(n.state, x, n.now(), cycle.REVIEWERS)[0]
                    for x in lifecycle.declared(n.state)}
        finally:
            n.close()
