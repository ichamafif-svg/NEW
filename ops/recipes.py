"""Recipes: repairs whose content is a pure function of the base tree and trusted data.

Rule 5 (round 2 of the M2 review): autonomy is reproducibility. An agent may merge without a human only a commit that
an independent instrument recomputes byte for byte from the base and trusted data. A recipe is that function: the
agent runs it to build the commit; the scanner's measure job runs it again, from its own reading of the base, and
compares with the commit's whole tree. Repairs that need judgment (a model's code change) have no recipe: they are
proposed, and only a human's signed review lets them merge.

A tree is anything with `paths()` and `read(path) -> bytes`."""
from __future__ import annotations

import json
import re

from packaging.version import InvalidVersion, Version

PIN = re.compile(r"^([A-Za-z0-9_.-]+)==([A-Za-z0-9_.+-]+)(\s*(#.*)?)$")
USES = re.compile(r"^(\s*-?\s*uses:\s*)([A-Za-z0-9_.-]+/[A-Za-z0-9_./-]+)@([^\s#]+)(.*)$")
SHA = re.compile(r"^[0-9a-f]{40}$")


def lock(tree) -> dict:
    out = {}
    for line in tree.read("requirements.txt").decode().splitlines():
        m = PIN.match(line.strip())
        if m:
            out[m[1].lower()] = m[2]
    return out


def vulns(tree, advisories: dict):
    """advisories: package -> [[fix versions of one vulnerability], ...] for the base lock. Each vulnerable pin moves to
    the smallest version that is at least one fix of every vulnerability; no fix for one of them: no recipe."""
    text = tree.read("requirements.txt").decode()
    target = {}
    for name, vulns_ in advisories.items():
        try:
            mins = [min(Version(v) for v in fixes) for fixes in vulns_]
        except (ValueError, InvalidVersion):
            return None
        target[name.lower()] = str(max(mins))
    if not target:
        return None
    lines = []
    for line in text.splitlines():
        m = PIN.match(line.strip())
        lines.append(f"{m[1]}=={target[m[1].lower()]}{m[3]}" if m and m[1].lower() in target else line)
    return {"requirements.txt": ("\n".join(lines) + "\n").encode()}


def sbom(tree, _data=None):
    doc = {"bomFormat": "CycloneDX", "specVersion": "1.5", "components": [
        {"type": "library", "name": n, "version": v, "purl": f"pkg:pypi/{n}@{v}"} for n, v in sorted(lock(tree).items())]}
    return {"sbom.json": (json.dumps(doc, indent=2) + "\n").encode()}


def actions(tree, resolve):
    """Pin every `uses: owner/repo@ref` to the commit the ref names today; the ref stays as a comment."""
    out = {}
    for path in sorted(tree.paths()):
        if not re.fullmatch(r"\.github/workflows/[^/]+\.ya?ml", path):
            continue
        lines, changed = [], False
        for line in tree.read(path).decode().splitlines():
            m = USES.match(line)
            if m and not SHA.fullmatch(m[3]):
                repo = "/".join(m[2].split("/")[:2])
                line, changed = f"{m[1]}{m[2]}@{resolve(repo, m[3])} # {m[3]}", True
            lines.append(line)
        if changed:
            out[path] = ("\n".join(lines) + "\n").encode()
    return out or None


RECIPES = {"vulns": vulns, "sbom": sbom, "actions": actions}


def reproduces(expected: dict | None, base: dict, head: dict, read) -> str:
    """Compare a commit's whole tree with its base plus the recipe's files. `base`/`head`: path -> blob id; `read`
    returns a blob's bytes. Every path of either tree is compared: additions, deletions and renames all count."""
    expected = {p: c for p, c in (expected or {}).items() if p not in base or read(base[p]) != c}
    if not expected:
        return "no:recipe"
    changed = {p for p in base.keys() | head.keys() if base.get(p) != head.get(p)}
    if changed != set(expected):
        return "no:paths"
    if any(p not in head or read(head[p]) != expected[p] for p in expected):
        return "no:content"
    return "yes"
