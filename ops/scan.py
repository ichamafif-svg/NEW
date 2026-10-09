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
    found = {}
    for line in (repo / "requirements.txt").read_text().splitlines():
        m = PIN.match(line.split("#")[0].strip())
        if m:
            found[m[1].lower()] = m[2]
    return found


def pypi(name):
    with urllib.request.urlopen(f"https://pypi.org/pypi/{name}/json", timeout=30) as r:
        return json.loads(r.read())


def vulns(repo):
    r = _run([sys.executable, "-m", "pip_audit", "-r", "requirements.txt", "-f", "json", "--progress-spinner", "off"], repo)
    data = json.loads(r.stdout or "{}")
    found = [v["id"] for d in data.get("dependencies", []) for v in d.get("vulns", [])]
    return "none" if r.returncode in (0, 1) and not found else f"found:{len(found)}" if found else "error:pip-audit"


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
    return [repo / p for p in _run(["git", "ls-files"], repo).stdout.split() if (repo / p).is_file()]


def secrets(repo):
    hits = sum(1 for p in tracked(repo) if p.stat().st_size < 1_000_000
               for rx in SECRETS if rx.search(p.read_text(errors="ignore")))
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
    run = gh.latest_run(workflow, "main")
    return "unknown" if run is None else "green" if run["conclusion"] == "success" else run["conclusion"] or "running"


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


def pull_facts(gh, agent_login: str, ci_names=("test",)) -> list:
    """For each open agent pull request: (resource, property, status) about its exact head commit."""
    facts = []
    for pr in gh.pulls():
        m = BRANCH.match(pr["head"]["ref"])
        if not m:
            continue
        sha, num = pr["head"]["sha"], str(pr["number"])
        resource = f"repo:{m[1]}:{m[2]}/pr/{num}/{sha}"
        runs = [r for r in gh.check_runs(sha) if r["name"] in ci_names]
        status = ("green" if runs and all(r["conclusion"] == "success" for r in runs)
                  else "red" if any(r["conclusion"] not in (None, "success") for r in runs) else "pending")
        files = gh.files(num)
        scope = "dependencies" if files and all(DEPENDENCY_FILES.match(f) for f in files) else "code"
        approved = any(r["state"] == "APPROVED" and r["commit_id"] == sha and r["user"]["login"] != agent_login
                       for r in gh.reviews(num))
        facts += [(resource, "ci", status), (resource, "scope", scope)]
        if approved:
            facts.append((resource, "review", "approved"))
    return facts
