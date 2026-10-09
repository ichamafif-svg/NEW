"""The scanner: an independent oracle that measures the repository and signs what it saw.

Outside the TCB, but it is a declared source: the law trusts its observations at level `real` only through the grant
humans gave it, and never lets the agent's own chain stand in for it. Each probe returns the status a floor target
expects, or something else that keeps the gap open. A probe that cannot run returns `error:<why>`; the inventory is
observed complete only when every probe ran."""
from __future__ import annotations

import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

DEPENDENCY_FILES = re.compile(r"^(requirements[^/]*\.txt|pyproject\.toml|poetry\.lock|uv\.lock|sbom\.json)$")
LICENSES = ("MIT", "BSD", "Apache", "ISC", "PSF", "Python Software Foundation", "MPL", "Unlicense", "Zlib")
SECRETS = [re.compile(p) for p in (
    r"AKIA[0-9A-Z]{16}", r"-----BEGIN (?:RSA |EC |OPENSSH |)PRIVATE KEY-----", r"gh[pousr]_[A-Za-z0-9]{36,}",
    r"sk-ant-[A-Za-z0-9_-]{20,}", r"xox[baprs]-[A-Za-z0-9-]{10,}",
    r"(?i)(?:api[_-]?key|secret|password|token)\s*[:=]\s*['\"][A-Za-z0-9/+_=-]{16,}['\"]")]
PIN = re.compile(r"^([A-Za-z0-9_.-]+)==([A-Za-z0-9_.+-]+)$")


def _run(cmd, cwd):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=600)


def pins(repo: Path) -> dict:
    """requirements.txt must be a full lock of exact pins: anything else (URL, range, option) is refused, since the
    audit never installs or resolves anything."""
    found = {}
    for line in (repo / "requirements.txt").read_text().splitlines():
        line = line.split("#")[0].strip()
        if not line:
            continue
        m = PIN.match(line)
        if not m:
            raise ValueError(f"not an exact pin: {line[:80]}")
        found[m[1].lower()] = m[2]
    return found


def pypi(name):
    with urllib.request.urlopen(f"https://pypi.org/pypi/{name}/json", timeout=30) as r:
        return json.loads(r.read())


def vulns(repo):
    pins(repo)                                            # refuses anything pip-audit would skip or resolve
    r = _run([sys.executable, "-m", "pip_audit", "-r", "requirements.txt", "--no-deps", "--disable-pip",
              "-f", "json", "--progress-spinner", "off"], repo)
    data = json.loads(r.stdout) if r.returncode in (0, 1) and r.stdout.strip() else None
    if not isinstance(data, dict) or not isinstance(data.get("dependencies"), list):
        return "error:pip-audit"
    if any("skip_reason" in d for d in data["dependencies"]) or len(data["dependencies"]) != len(pins(repo)):
        return "error:not-audited"
    found = [v["id"] for d in data["dependencies"] for v in d.get("vulns", [])]
    return "none" if not found else f"found:{len(found)}"


def deps_age(repo):
    behind = [n for n, v in pins(repo).items()
              if v.split(".")[0].isdigit() and int(pypi(n)["info"]["version"].split(".")[0]) > int(v.split(".")[0])]
    return "none" if not behind else f"found:{len(behind)}"


def licenses(repo):
    bad = []
    for n in pins(repo):
        info = pypi(n)["info"]
        text = " ".join([info.get("license") or "", info.get("license_expression") or "", *info.get("classifiers", [])])
        if not any(l in text for l in LICENSES):
            bad.append(n)
    return "compliant" if not bad else f"review:{len(bad)}"


def tracked(repo):
    names = _run(["git", "ls-files", "-z"], repo).stdout.split("\0")
    return [repo / p for p in names if p and (repo / p).is_file() and not (repo / p).is_symlink()]


def secrets(repo):
    files = tracked(repo)
    if any(p.stat().st_size >= 5_000_000 for p in files):
        return "error:file-too-large"                     # unscanned is a gap, never a pass
    hits = sum(1 for p in files for rx in SECRETS if rx.search(p.read_text(errors="ignore")))
    return "none" if not hits else f"found:{hits}"


def sast(repo):
    r = _run([sys.executable, "-m", "bandit", "-r", ".", "-x", "./tests,./.venv", "-f", "json", "-q", "-lll"], repo)
    data = json.loads(r.stdout or "{}")
    if "results" not in data:
        return "error:bandit"
    return "none" if not data["results"] else f"found:{len(data['results'])}"


def actions(repo):
    loose = [u for p in (repo / ".github" / "workflows").glob("*.y*ml") for u in
             re.findall(r"uses:\s*([^\s#]+)", p.read_text()) if not u.startswith("./") and not re.search(r"@[0-9a-f]{40}$", u)]
    return "all" if not loose else f"unpinned:{len(loose)}"


def sbom_components(repo) -> list:
    return [{"type": "library", "name": n, "version": v, "purl": f"pkg:pypi/{n}@{v}"} for n, v in sorted(pins(repo).items())]


def sbom(repo):
    path = repo / "sbom.json"
    if not path.exists():
        return "missing"
    doc = json.loads(path.read_text())
    have = sorted((c["name"], c["version"]) for c in doc.get("components", []))
    return "current" if have == [(c["name"], c["version"]) for c in sbom_components(repo)] else "stale"


def ci(gh, workflow="ci.yml"):
    """The push run of this repository at the current head of main, nothing else (not a fork branch named main)."""
    head = gh.get("/branches/main")["commit"]["sha"]
    runs = [r for r in gh.get(f"/actions/workflows/{workflow}/runs", branch="main", event="push", head_sha=head,
                               per_page=20).get("workflow_runs", [])
            if r.get("head_repository", {}).get("full_name") == gh.repo and r["head_sha"] == head]
    if not runs:
        return "unknown"
    return "green" if runs[0]["conclusion"] == "success" else runs[0]["conclusion"] or "running"


def branch(gh):
    kinds = {r["type"] for r in gh.rules("main")}
    return "pr-and-checks" if {"pull_request", "required_status_checks"} <= kinds else "missing:" + ",".join(
        sorted({"pull_request", "required_status_checks"} - kinds))


TARGETS = {"vulns": vulns, "deps-age": deps_age, "licenses": licenses, "secrets": secrets, "sast": sast,
           "actions": actions, "sbom": sbom}


def measure(repo: Path, gh) -> dict:
    """target id -> status. An exception becomes an error status: a gap, never a pass."""
    out = {}
    for tid, probe in TARGETS.items():
        try:
            out[tid] = probe(repo)
        except Exception as exc:  # noqa: BLE001
            out[tid] = f"error:{type(exc).__name__}"
    for tid, probe in (("ci", ci), ("branch", branch)):
        try:
            out[tid] = probe(gh)
        except Exception as exc:  # noqa: BLE001
            out[tid] = f"error:{type(exc).__name__}"
    return out


BRANCH = re.compile(r"^standard/([a-z]+)/([a-z-]+)/[0-9a-f]{8}$")


def _approved(gh, number, sha) -> bool:
    """Latest review of each reviewer with write access; any standing change request blocks."""
    latest = {}
    for r in gh.reviews(number):
        if r["state"] in ("APPROVED", "CHANGES_REQUESTED", "DISMISSED"):
            latest[r["user"]["login"]] = r
    if any(r["state"] == "CHANGES_REQUESTED" for r in latest.values()):
        return False
    return any(r["state"] == "APPROVED" and r["commit_id"] == sha and gh.can_write(login)
               for login, r in latest.items())


def pull_facts(gh, agent_login: str, ci_names=("test",), limit=20) -> list:
    """For each open pull request of the agent itself, from this repository, into main: facts about its head commit.
    Pull requests of anyone else are never observed: an outsider cannot borrow the agent's autonomy."""
    facts = []
    mine = [pr for pr in gh.pulls() if pr["user"]["login"] == agent_login and pr["base"]["ref"] == "main"
            and (pr["head"].get("repo") or {}).get("full_name") == gh.repo and BRANCH.match(pr["head"]["ref"])]
    for pr in mine[:limit]:
        m = BRANCH.match(pr["head"]["ref"])
        sha, num = pr["head"]["sha"], str(pr["number"])
        resource = f"repo:{m[1]}:{m[2]}/pr/{num}/{sha}"
        runs = [r for r in gh.check_runs(sha) if r["name"] in ci_names]
        status = ("green" if runs and all(r["conclusion"] == "success" for r in runs)
                  else "red" if any(r["conclusion"] not in (None, "success") for r in runs) else "pending")
        files, detail = gh.files(num), gh.pull(num)
        scope = ("dependencies" if files and len(files) == detail.get("changed_files")
                 and all(DEPENDENCY_FILES.match(f) for f in files) else "code")
        facts += [(resource, "ci", status), (resource, "scope", scope)]
        if _approved(gh, num, sha):
            facts.append((resource, "review", "approved"))
    return facts
