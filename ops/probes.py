"""Probes: what the scanner measures, and the single rule that turns a measure into a signed status.

Principle (cause 2 of the M2 review): absence of a finding is not a pass. A probe returns its universe (what it had
to examine), what it actually covered, and what it found. Only `verdict` writes a status, and it writes the floor's
expected status only when the whole, non-empty universe was covered and nothing was found. A probe that raises,
skips an element or examines nothing yields `uncovered`, a gap the scanner owns; `found` is a gap an agent may repair.
The probes never install, import or run the code they examine."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from .world import pypi

PIN = re.compile(r"^([A-Za-z0-9_.-]+)==([A-Za-z0-9_.+-]+)$")
LICENSES = ("MIT", "BSD", "Apache", "ISC", "PSF", "Python Software Foundation", "MPL", "Unlicense", "Zlib")
SECRETS = [re.compile(p) for p in (
    r"AKIA[0-9A-Z]{16}", r"-----BEGIN (?:RSA |EC |OPENSSH |)PRIVATE KEY-----", r"gh[pousr]_[A-Za-z0-9]{36,}",
    r"sk-ant-[A-Za-z0-9_-]{20,}", r"xox[baprs]-[A-Za-z0-9-]{10,}",
    r"(?i)(?:api[_-]?key|secret|password|token)\s*[:=]\s*['\"][A-Za-z0-9/+_=-]{16,}['\"]")]
MAX_TEXT = 5_000_000


@dataclass(frozen=True)
class Measure:
    universe: frozenset
    covered: frozenset
    findings: tuple = ()


def verdict(expect: str, measure) -> str:
    """The only place a status is decided. `measure` is a Measure or the exception the probe raised."""
    if isinstance(measure, BaseException):
        return f"uncovered:{type(measure).__name__}"
    if not measure.universe:
        return "uncovered:empty"
    missing = measure.universe - measure.covered
    if missing:
        return f"uncovered:{len(missing)}"
    return f"found:{len(measure.findings)}" if measure.findings else expect


def repairable(status: str) -> bool:
    return status.startswith("found:")


def _run(cmd, cwd):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=600)


def lock(repo: Path) -> dict:
    """requirements.txt is a full lock of exact pins. A line that is not one is a finding of its own kind."""
    pins, bad = {}, []
    for line in (repo / "requirements.txt").read_text().splitlines():
        line = line.split("#")[0].strip()
        if line:
            m = PIN.match(line)
            (pins.__setitem__(m[1].lower(), m[2]) if m else bad.append(line[:80]))
    if bad:
        raise ValueError(f"not exact pins: {bad[:3]}")
    return pins


def tracked(repo: Path) -> list:
    names = _run(["git", "ls-files", "-z"], repo).stdout.split("\0")
    return [p for p in names if p and (repo / p).is_file() and not (repo / p).is_symlink()]


def text_files(repo: Path) -> list:
    out = []
    for p in tracked(repo):
        with (repo / p).open("rb") as f:
            if b"\0" not in f.read(8192):
                out.append(p)
    return out


# ---- probes: repo -> Measure ----------------------------------------------------------------------------------
def vulns(repo, world=None):
    pins = lock(repo)
    r = _run([sys.executable, "-m", "pip_audit", "-r", "requirements.txt", "--no-deps", "--disable-pip",
              "-f", "json", "--progress-spinner", "off"], repo)
    deps = json.loads(r.stdout)["dependencies"]
    audited = {d["name"].lower() for d in deps if "skip_reason" not in d}
    return Measure(frozenset(pins), frozenset(audited & set(pins)),
                   tuple(v["id"] for d in deps for v in d.get("vulns", [])))


def deps_age(repo, world=None):
    pins, covered, behind = lock(repo), set(), []
    for name, version in pins.items():
        latest = pypi(name)["version"]
        covered.add(name)
        if latest.split(".")[0].isdigit() and version.split(".")[0].isdigit() and \
                int(latest.split(".")[0]) > int(version.split(".")[0]):
            behind.append(name)
    return Measure(frozenset(pins), frozenset(covered), tuple(behind))


def licenses(repo, world=None):
    pins, covered, bad = lock(repo), set(), []
    for name in pins:
        info = pypi(name)
        text = " ".join([info.get("license") or "", info.get("license_expression") or "", *info.get("classifiers", [])])
        covered.add(name)
        if not any(x in text for x in LICENSES):
            bad.append(name)
    return Measure(frozenset(pins), frozenset(covered), tuple(bad))


def secrets(repo, world=None):
    files, covered, hits = text_files(repo), set(), []
    for p in files:
        if (repo / p).stat().st_size < MAX_TEXT:
            text = (repo / p).read_text(errors="ignore")
            covered.add(p)
            hits += [p for rx in SECRETS if rx.search(text)]
    return Measure(frozenset(files), frozenset(covered), tuple(hits))


def sast(repo, world=None):
    files = [p for p in tracked(repo) if p.endswith(".py") and not p.startswith("tests/")]
    r = _run([sys.executable, "-m", "bandit", "-f", "json", "-q", *files], repo)
    data = json.loads(r.stdout)
    covered = {k.removeprefix("./") for k in data["metrics"] if k != "_totals"} - {e["filename"] for e in data["errors"]}
    high = [x["test_id"] for x in data["results"] if x["issue_severity"] == "HIGH"]
    return Measure(frozenset(files), frozenset(covered) & frozenset(files), tuple(high))


def actions(repo, world=None):
    flows = sorted(p for p in tracked(repo) if re.fullmatch(r"\.github/workflows/[^/]+\.ya?ml", p))
    loose = [u for p in flows for u in re.findall(r"uses:\s*([^\s#]+)", (repo / p).read_text())
             if not u.startswith("./") and not re.search(r"@[0-9a-f]{40}$", u)]
    return Measure(frozenset(flows), frozenset(flows), tuple(loose))


def sbom_document(repo) -> dict:
    return {"bomFormat": "CycloneDX", "specVersion": "1.5", "components": [
        {"type": "library", "name": n, "version": v, "purl": f"pkg:pypi/{n}@{v}"} for n, v in sorted(lock(repo).items())]}


def sbom(repo, world=None):
    pins = lock(repo)
    path = repo / "sbom.json"
    listed = {(c["name"], c["version"]) for c in json.loads(path.read_text())["components"]} if path.exists() else set()
    return Measure(frozenset(pins), frozenset(pins), tuple(n for n, v in pins.items() if (n, v) not in listed))


def ci(repo, world):
    head = world.main_head()
    conclusion = world.ci(head)
    return Measure(frozenset({head}), frozenset({head} if conclusion else ()),
                   () if conclusion == "success" else (conclusion,))


def branch(repo, world):
    need = frozenset({"pull_request", "required_status_checks"})
    return Measure(need, need, tuple(sorted(need - world.rule_types())))


PROBES = {"vulns": vulns, "deps-age": deps_age, "licenses": licenses, "secrets": secrets, "sast": sast,
          "actions": actions, "sbom": sbom, "ci": ci, "branch": branch}


def measure_all(repo: Path, world, targets: dict) -> dict:
    """target id -> status, every probe through `verdict`."""
    out = {}
    for tid, probe in PROBES.items():
        try:
            m = probe(repo, world)
        except Exception as exc:  # noqa: BLE001 - an exception is a measure: nothing was covered
            m = exc
        out[tid] = verdict(targets[tid]["expect"], m)
    return out
