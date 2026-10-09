"""Regressions for the independent adversarial review of M2 (docs/M2.md, "Revue adversariale")."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))
from fixture import raises, run  # noqa: E402
from ops import agent, cycle, node as node_mod, scan  # noqa: E402
from ops.node import Node, load_keys  # noqa: E402
from test_ops import HEAD, Clock, FakeGH, args, setup  # noqa: E402

AGENT = "standard-agent[bot]"


class PRs:
    """A GitHub where pull requests, files, reviews and permissions are scripted."""
    repo = "o/demo"

    def __init__(self, pulls, files=None, reviews=None, writers=("maintainer",), changed=None):
        self._pulls, self._files, self._reviews = pulls, files or {}, reviews or {}
        self.writers, self.changed = set(writers), changed or {}

    def authored(self, login, limit):
        return [p for p in self._pulls if p["user"]["login"] == login][:limit]

    def check_runs(self, sha):
        return [{"name": "test", "conclusion": "success"}]

    def files(self, n):
        return self._files.get(n, ["requirements.txt"])

    def pull(self, n):
        return {"changed_files": self.changed.get(n, len(self.files(n)))}

    def flood(self, n):
        self._pulls = [pr(1000 + i, login="spammer") for i in range(n)] + self._pulls

    def reviews(self, n):
        return self._reviews.get(n, [])

    def can_write(self, login):
        return login in self.writers


def pr(num, login=AGENT, repo="o/demo", base="main", ref="standard/deps/vulns/abcd1234"):
    return {"number": num, "state": "open", "user": {"login": login}, "base": {"ref": base},
            "head": {"ref": ref, "sha": HEAD, "repo": {"full_name": repo}}}


def test_only_the_agents_own_pull_requests_into_main_are_observed():
    gh = PRs([pr(1, login="outsider"), pr(2, repo="evil/fork"), pr(3, base="standard-journal"), pr(4)])
    resources = {r for r, _, _ in scan.pull_facts(gh, AGENT)}
    assert resources == {f"repo:deps:vulns/pr/4/{HEAD}"}, resources


def test_a_review_counts_only_from_a_writer_on_this_commit_without_standing_objection():
    review = lambda login, state, sha=HEAD: {"user": {"login": login}, "state": state, "commit_id": sha}
    cases = {
        "sockpuppet": ([review("nobody", "APPROVED")], False),
        "writer": ([review("maintainer", "APPROVED")], True),
        "older commit": ([review("maintainer", "APPROVED", "d" * 40)], False),
        "objection": ([review("maintainer", "APPROVED"), review("other", "CHANGES_REQUESTED")], False),
        "withdrawn objection": ([review("maintainer", "CHANGES_REQUESTED"), review("maintainer", "APPROVED")], True),
        "outsider objection": ([review("maintainer", "APPROVED"), review("drive-by", "CHANGES_REQUESTED")], True),
    }
    for name, (reviews, expected) in cases.items():
        gh = PRs([pr(4)], reviews={"4": reviews}, writers=("maintainer", "other"))
        got = (f"repo:deps:vulns/pr/4/{HEAD}", "review", "approved") in scan.pull_facts(gh, AGENT)
        assert got is expected, name


def test_a_flood_of_other_pull_requests_hides_nothing():
    gh = PRs([pr(4)])
    gh.flood(5000)
    assert {r for r, _, _ in scan.pull_facts(gh, AGENT)} == {f"repo:deps:vulns/pr/4/{HEAD}"}
    assert [p["number"] for p in scan.agent_pulls(gh, AGENT)] == [4]


def test_a_truncated_file_list_is_never_dependency_scope():
    gh = PRs([pr(4)], files={"4": ["requirements.txt"]}, changed={"4": 2})
    assert (f"repo:deps:vulns/pr/4/{HEAD}", "scope", "code") in scan.pull_facts(gh, AGENT)


def repo_with(files: dict) -> Path:
    d = Path(tempfile.mkdtemp())
    for name, text in files.items():
        (d / name).write_text(text)
    subprocess.run(["git", "init", "-q"], cwd=d, check=True)
    subprocess.run(["git", "add", "-A"], cwd=d, check=True)
    return d


def test_an_unaudited_dependency_or_a_failed_audit_is_a_gap():
    with raises(ValueError, "exact pin"):
        scan.vulns(repo_with({"requirements.txt": "pkg @ https://evil.invalid/x.whl\n"}))
    failed = SimpleNamespace(returncode=1, stdout="")
    with patch.object(scan, "_run", lambda cmd, cwd: failed):
        assert scan.vulns(repo_with({"requirements.txt": "flask==2.2.2\n"})) == "error:pip-audit"
    skipped = SimpleNamespace(returncode=0, stdout=json.dumps({"dependencies": [{"name": "flask", "skip_reason": "x"}]}))
    with patch.object(scan, "_run", lambda cmd, cwd: skipped if "pip_audit" in cmd else subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True)):
        assert scan.vulns(repo_with({"requirements.txt": "flask==2.2.2\n"})) == "error:not-audited"


def test_secrets_in_files_with_spaces_are_found_and_binaries_do_not_block():
    repo = repo_with({"my config.py": 'API_KEY = "abcdefghijklmnop1234"\n'})
    assert scan.secrets(repo).startswith("found:")
    big = repo_with({"ok.py": "x = 1\n"})
    (big / "logo.png").write_bytes(b"\x89PNG\0" + b"\0" * 6_000_000)
    subprocess.run(["git", "add", "-A"], cwd=big, check=True)
    assert scan.secrets(big) == "none"


def test_the_agent_never_writes_git_internals_or_outside_the_tree():
    repo = repo_with({"app.py": "x = 1\n"})
    (repo / "meta").symlink_to(repo / ".git")
    for path in (".git/config", "a/.git/hooks/pre-commit", "../escape.py", "/etc/passwd", ".gitattributes",
                 "meta/config"):
        with raises(ValueError, "may not write"):
            agent.allowed(repo, path, "sast")
    assert agent.allowed(repo, "app.py", "sast") == (repo / "app.py").resolve()


def test_a_replaced_state_is_refused_without_the_external_genesis_pin():
    tmp = tempfile.mkdtemp()
    keyfile, publics = setup(tmp)
    state = str(Path(tmp) / "state")
    n = Node(state, load_keys(keyfile), create=True)
    try:
        cycle.cmd_init(n, args(state, publics=publics))
    finally:
        n.close()
    real = json.loads(Path(state, "genesis.json").read_text())["pin"]
    with raises(ValueError, "externally pinned genesis"):
        Node(state, load_keys(keyfile))
    with raises(ValueError, "externally pinned genesis"):
        Node(state, load_keys(keyfile), expected_genesis="sha256:" + "1" * 64)
    Node(state, load_keys(keyfile), expected_genesis=real).close()


def test_a_child_route_needs_a_typed_child():
    from tcb.law import _ops, _reaches
    ops = _ops({"noop": {"args": {"x": "segment"}, "resource": "{x}/noop", "profile": "capability"}})
    assert not _reaches(ops["noop"], "payroll")


def test_a_refused_merge_is_asked_again_and_an_unknown_one_is_reconciled():
    tmp = tempfile.mkdtemp()
    keyfile, publics = setup(tmp)
    state = str(Path(tmp) / "state")
    clock, gh = Clock(), FakeGH()
    keys = load_keys(keyfile)
    resource = f"repo:deps:vulns/pr/7/{HEAD}"
    facts = [(resource, "ci", "green"), (resource, "scope", "dependencies")]
    outcomes = []

    def step(command):
        pinned = Path(state, "genesis.json")
        expected = json.loads(pinned.read_text())["pin"] if pinned.exists() else None
        n = Node(state, keys, create=command == "init", expected_genesis=expected)
        try:
            getattr(cycle, "cmd_" + command)(n, args(state, publics=publics))
            return n.state
        finally:
            n.close()

    def merge(resource_, args_, key):
        result = outcomes.pop(0)
        gh.merged = result == "ok-late"
        return "unknown" if result == "ok-late" else result

    with patch.object(node_mod.time, "time", clock), patch.object(cycle.time, "time", clock), \
            patch.dict("os.environ", {"GITHUB_TOKEN": "x", "MERGE_TOKEN": "z"}), \
            patch("ops.gh.Client", lambda repo, token: gh), \
            patch.object(scan, "measure", lambda repo, g: {}), \
            patch.object(scan, "pull_facts", lambda g, login: list(facts)), \
            patch("adapters.github.GitHub.remediate", lambda self, r, a, k: merge(r, a, k)):
        step("init")
        clock.t += 3_700
        step("activate")
        step("scan")
        step("ask")
        outcomes.append("failed")
        s = step("guard")
        first = next(iter(s["intents"]))
        assert s["line"][first]["state"] == "failed"
        s = step("ask")
        assert len(s["intents"]) == 1, "no retry without a newer observation of the commit"
        clock.t += 7 * 3_600                                   # the scanner refreshes its facts
        step("scan")
        s = step("ask")
        retry = next(i for i in s["intents"] if i != first)
        assert s["intents"][retry]["stmt"]["retry_of"] == first
        outcomes.append("ok-late")                              # merged, but the adapter could not tell
        s = step("guard")
        assert s["line"][retry]["state"] == "uncertain"
        s = step("scan")
        assert s["line"][retry]["state"] == "proving" and f"proof:{retry}" not in s["obligations"]



def test_a_guard_that_dies_after_its_reservation_does_not_stall_the_target():
    class Crash(BaseException):
        pass
    tmp = tempfile.mkdtemp()
    keyfile, publics = setup(tmp)
    state = str(Path(tmp) / "state")
    clock, gh = Clock(), FakeGH()
    keys = load_keys(keyfile)
    resource = f"repo:deps:vulns/pr/7/{HEAD}"
    facts = [(resource, "ci", "green"), (resource, "scope", "dependencies")]

    def step(command):
        pinned = Path(state, "genesis.json")
        expected = json.loads(pinned.read_text())["pin"] if pinned.exists() else None
        n = Node(state, keys, create=command == "init", expected_genesis=expected)
        try:
            getattr(cycle, "cmd_" + command)(n, args(state, publics=publics))
            return n.state
        finally:
            n.close()

    def dies(*a):
        raise Crash()
    with patch.object(node_mod.time, "time", clock), patch.object(cycle.time, "time", clock), \
            patch.dict("os.environ", {"GITHUB_TOKEN": "x", "MERGE_TOKEN": "z"}), \
            patch("ops.gh.Client", lambda repo, token: gh), \
            patch.object(scan, "measure", lambda repo, g: {}), \
            patch.object(scan, "pull_facts", lambda g, login: list(facts)):
        step("init")
        clock.t += 3_700
        step("activate")
        step("scan")
        s = step("ask")
        first = next(iter(s["intents"]))
        with patch("tcb.effects.EffectPort.perform", dies):
            try:
                step("guard")
            except Crash:
                pass
        clock.t += 7 * 3_600                                   # past the dispatch window; facts refreshed
        s = step("scan")
        assert s["line"][first]["state"] == "failed", s["line"][first]   # reconciled: not applied
        s = step("ask")
        assert any(it["stmt"].get("retry_of") == first for it in s["intents"].values())


if __name__ == "__main__":
    run(globals())
