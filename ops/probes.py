"""Probes: what the scanner measures about main, and the single rule that turns a measure into a signed status.

Rule 2: a pass is a proof of coverage. A probe returns its universe, what it covered and what it found; only
`verdict` writes a status, the floor's expected one only when the whole non-empty universe was covered without
finding. An exception, a skipped element or an empty universe is `uncovered`.

Rule 5: the instrument and its universe are fixed by Standard, never by the content measured. Every tracked file is
in the secrets universe whatever its bytes; every `uses` anywhere in a parsed workflow counts; bandit ignores
`# nosec`; the lock is the dependency universe and any other dependency manifest makes it uncovered. Probes read
content; they never install, import or run it (code that runs is measured apart, by ops.testrun, without keys)."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

from .world import pypi

PIN = re.compile(r"^([A-Za-z0-9_.-]+)==([A-Za-z0-9_.+-]+)$")
PERMISSIVE = {"MIT", "BSD-2-Clause", "BSD-3-Clause", "Apache-2.0", "ISC", "PSF-2.0", "MPL-2.0", "Unlicense", "Zlib"}
PERMISSIVE_CLASSIFIERS = {"License :: OSI Approved :: MIT License", "License :: OSI Approved :: BSD License",
                          "License :: OSI Approved :: Apache Software License", "License :: OSI Approved :: ISC License (ISCL)",
                          "License :: OSI Approved :: Python Software Foundation License",
                          "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
                          "License :: OSI Approved :: The Unlicense (Unlicense)", "License :: OSI Approved :: zlib/libpng License"}
OTHER_MANIFESTS = ("setup.py", "setup.cfg", "Pipfile", "Pipfile.lock", "poetry.lock", "uv.lock")
SECRETS = [re.compile(p) for p in (
    rb"AKIA[0-9A-Z]{16}", rb"-----BEGIN (?:RSA |EC |OPENSSH |)PRIVATE KEY-----", rb"gh[pousr]_[A-Za-z0-9]{36,}",
    rb"sk-ant-[A-Za-z0-9_-]{20,}", rb"xox[baprs]-[A-Za-z0-9-]{10,}",
    rb"(?i)(?:api[_-]?key|secret|password|token)\s*[:=]\s*['\"][A-Za-z0-9/+_=-]{16,}['\"]")]
MAX_FILE = 5_000_000


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
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=900)


class Checkout:
    """A tree on disk: the tracked files of a git checkout, read as bytes."""

    def __init__(self, root):
        self.root = Path(root)
        names = _run(["git", "ls-files", "-z"], self.root).stdout.split("\0")
        self._paths = {p for p in names if p}

    def paths(self):
        return set(self._paths)

    def read(self, path):
        full = self.root / path
        if path not in self._paths or full.is_symlink():
            raise FileNotFoundError(path)
        return full.read_bytes()


def lock(tree) -> dict:
    """The dependency universe: requirements.txt as a full lock of exact pins, and no other manifest."""
    present = [m for m in OTHER_MANIFESTS if m in tree.paths()]
    if "pyproject.toml" in tree.paths() and re.search(rb"(?m)^\s*(dependencies|requires)\s*=", tree.read("pyproject.toml")):
        present.append("pyproject.toml")
    if present:
        raise ValueError(f"dependencies declared outside the lock: {present}")
    pins, bad = {}, []
    for line in tree.read("requirements.txt").decode().splitlines():
        line = line.split("#")[0].strip()
        if line:
            m = PIN.match(line)
            (pins.__setitem__(m[1].lower(), m[2]) if m else bad.append(line[:80]))
    if bad:
        raise ValueError(f"not exact pins: {bad[:3]}")
    return pins


def audit(tree) -> list:
    """pip-audit of the lock, without installing or resolving anything."""
    lock(tree)
    r = _run([sys.executable, "-m", "pip_audit", "-r", "requirements.txt", "--no-deps", "--disable-pip",
              "-f", "json", "--progress-spinner", "off"], tree.root)
    return json.loads(r.stdout)["dependencies"]


def advisories(deps: list) -> dict:
    return {d["name"].lower(): [v["fix_versions"] for v in d["vulns"]] for d in deps if d.get("vulns")}


# ---- probes: (tree, ctx) -> Measure ---------------------------------------------------------------------------
def vulns(tree, ctx):
    pins, deps = lock(tree), ctx["audit"]()
    audited = {d["name"].lower() for d in deps if "skip_reason" not in d}
    return Measure(frozenset(pins), frozenset(audited & set(pins)),
                   tuple(v["id"] for d in deps for v in d.get("vulns", [])))


def deps_age(tree, ctx):
    pins, covered, behind = lock(tree), set(), []
    for name, version in pins.items():
        latest = pypi(name)["version"]
        covered.add(name)
        if latest.split(".")[0].isdigit() and version.split(".")[0].isdigit() and \
                int(latest.split(".")[0]) > int(version.split(".")[0]):
            behind.append(name)
    return Measure(frozenset(pins), frozenset(covered), tuple(behind))


def licenses(tree, ctx):
    pins, covered, bad = lock(tree), set(), []
    for name in pins:
        info = pypi(name)
        ok = (info.get("license_expression") in PERMISSIVE
              or bool(PERMISSIVE_CLASSIFIERS & set(info.get("classifiers") or [])))
        covered.add(name)
        if not ok:
            bad.append(name)
    return Measure(frozenset(pins), frozenset(covered), tuple(bad))


def secrets(tree, ctx):
    files, covered, hits = tree.paths(), set(), []
    for p in files:
        data = tree.read(p)
        if len(data) < MAX_FILE:
            covered.add(p)
            hits += [p for rx in SECRETS if rx.search(data)]
    return Measure(frozenset(files), frozenset(covered), tuple(hits))


def sast(tree, ctx):
    files = sorted(p for p in tree.paths() if p.endswith(".py"))
    r = _run([sys.executable, "-m", "bandit", "--ignore-nosec", "-f", "json", "-q", *files], tree.root)
    data = json.loads(r.stdout)
    covered = {k.removeprefix("./") for k in data["metrics"] if k != "_totals"} - {e["filename"] for e in data["errors"]}
    high = [x["test_id"] for x in data["results"] if x["issue_severity"] == "HIGH"]
    return Measure(frozenset(files), frozenset(covered) & frozenset(files), tuple(high))


def _uses(node):
    if isinstance(node, dict):
        for k, v in node.items():
            if k == "uses" and isinstance(v, str):
                yield v
            yield from _uses(v)
    elif isinstance(node, list):
        for v in node:
            yield from _uses(v)


def actions(tree, ctx):
    files = sorted(p for p in tree.paths() if re.fullmatch(r"\.github/workflows/[^/]+\.ya?ml", p)
                   or re.fullmatch(r"(.*/)?action\.ya?ml", p))
    covered, loose = set(), []
    for p in files:
        doc = yaml.safe_load(tree.read(p))
        covered.add(p)
        loose += [u for u in _uses(doc) if not u.startswith("./") and not re.search(r"@[0-9a-f]{40}$", u)]
    return Measure(frozenset(files), frozenset(covered), tuple(loose))


def sbom(tree, ctx):
    pins = lock(tree)
    listed = ({(c["name"], c["version"]) for c in json.loads(tree.read("sbom.json"))["components"]}
              if "sbom.json" in tree.paths() else set())
    return Measure(frozenset(pins), frozenset(pins), tuple(n for n, v in pins.items() if (n, v) not in listed))


def branch(tree, ctx):
    need = frozenset({"update", "deletion", "non_fast_forward"})
    return Measure(need, need, tuple(sorted(need - ctx["world"].rule_types())))


def lineage(tree, ctx):
    """Every commit on main since the anchor is the head of a judged effect: no change reached main around the law."""
    history = ctx["world"].history(ctx["anchor"], ctx["main"])
    return Measure(frozenset(history) | {ctx["main"]}, frozenset(history) | {ctx["main"]},
                   tuple(c for c in history if c not in ctx["judged"]))


PROBES = {"vulns": vulns, "deps-age": deps_age, "licenses": licenses, "secrets": secrets, "sast": sast,
          "actions": actions, "sbom": sbom, "branch": branch, "lineage": lineage}


def measure_all(tree, ctx, targets: dict) -> dict:
    """target id -> status, every probe through `verdict`. `ci` comes from ops.testrun, not from here."""
    out = {}
    for tid, probe in PROBES.items():
        try:
            m = probe(tree, ctx)
        except Exception as exc:  # noqa: BLE001 - an exception is a measure: nothing was covered
            m = exc
        out[tid] = verdict(targets[tid]["expect"], m)
    return out
