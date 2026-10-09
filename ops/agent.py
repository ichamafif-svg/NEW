"""The maintenance agent: prepares a repair as a pull request, then asks the law to merge its exact commit.

Untrusted by construction. It holds the agent key, a GitHub token that can push branches and open pull requests,
and a Claude API key. It cannot merge: only the guard, after both judges, sends `remediate`, and only for a commit the
scanner observed green and in scope. A bad patch is refused or reviewed; it is never a way around the law."""
from __future__ import annotations

import json
import os
import re
import subprocess
import urllib.request
import uuid
from pathlib import Path

from . import scan

API = "https://api.anthropic.com/v1/messages"
MODEL = os.environ.get("STANDARD_AGENT_MODEL", "claude-sonnet-5-5")
FORBIDDEN = re.compile(r"^(\.github/|\.standard/|standard-|control/)")
GUIDE = {
    "vulns": "Upgrade the vulnerable pinned dependencies in requirements.txt to the lowest fixed versions.",
    "deps-age": "Upgrade the pinned dependencies that are a major version behind, keeping the code working.",
    "licenses": "Replace dependencies whose license is not permissive, or explain why none is needed.",
    "secrets": "Remove the hard-coded secret and read it from an environment variable instead.",
    "sast": "Fix the high-severity issues reported by bandit without changing behaviour.",
    "ci": "Make the failing test suite pass by fixing the code, not by weakening tests.",
    "actions": "Pin every GitHub Action to a full commit SHA, with the version in a comment.",
    "sbom": "Regenerate sbom.json so that its components match requirements.txt exactly.",
}


def claude(prompt: str, key: str) -> dict:
    body = {"model": MODEL, "max_tokens": 16000, "messages": [{"role": "user", "content": prompt}],
            "system": "You are a careful maintenance engineer. Answer with one JSON object and nothing else."}
    req = urllib.request.Request(API, data=json.dumps(body).encode(), method="POST", headers={
        "x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        text = "".join(b.get("text", "") for b in json.loads(r.read())["content"])
    return json.loads(text[text.find("{"):text.rfind("}") + 1])


def context(repo: Path, limit=120_000) -> str:
    parts, size = [], 0
    for p in scan.tracked(repo):
        rel = p.relative_to(repo).as_posix()
        if FORBIDDEN.match(rel) or p.suffix not in (".py", ".txt", ".toml", ".json", ".md", ".yml", ".yaml", ".cfg"):
            continue
        text = p.read_text(errors="ignore")
        if size + len(text) > limit:
            break
        parts.append(f"=== {rel} ===\n{text}")
        size += len(text)
    return "\n".join(parts)


SAFE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]*(/[A-Za-z0-9_][A-Za-z0-9_.-]*)*$")


def allowed(repo: Path, path: str, target: str) -> Path:
    """A model reply names files; only plain paths inside the work tree, never git's own files or control files."""
    workflows = target == "actions" and re.fullmatch(r"\.github/workflows/[A-Za-z0-9_.-]+\.ya?ml", path)
    parts = path.split("/")
    if not (SAFE.fullmatch(path) or workflows) or any(p in ("", ".", "..") or p.lower().startswith(".git")
                                                       and not workflows for p in parts):
        raise ValueError(f"the agent may not write {path!r}")
    if FORBIDDEN.match(path) and not workflows:
        raise ValueError(f"the agent may not write {path!r}")
    walk = repo
    for part in parts:                                    # no component may be a link, before resolution hides it
        walk = walk / part
        if walk.is_symlink():
            raise ValueError(f"the agent may not write {path!r}")
    full = (repo / path).resolve()
    if repo.resolve() not in full.parents or ".git" in full.relative_to(repo.resolve()).parts or (
            full.exists() and not full.is_file()):
        raise ValueError(f"the agent may not write {path!r}")
    return full


def propose_patch(repo: Path, target: str, status: str, key: str) -> dict:
    prompt = (f"Repository files follow. The maintenance target `{target}` currently reads `{status}`.\n"
              f"Task: {GUIDE[target]}\nReturn JSON: {{\"title\": str, \"body\": str, \"files\": "
              f"{{path: full new content}}}}. Change as few files as possible. Never touch .github/ except for the "
              f"`actions` target.\n\n{context(repo)}")
    patch = claude(prompt, key)
    files = patch.get("files") or {}
    for path in files:
        allowed(repo, str(path), target)
    return {"title": str(patch.get("title", f"Remediate {target}"))[:200], "body": str(patch.get("body", ""))[:4000],
            "files": {str(k): str(v) for k, v in files.items()}}


def open_repair(repo: Path, gh, target: str, area: str, item: str, status: str, key: str) -> dict | None:
    if target == "sbom":                                   # deterministic: no model needed to list pinned packages
        doc = {"bomFormat": "CycloneDX", "specVersion": "1.5", "components": scan.sbom_components(repo)}
        patch = {"title": "Regenerate SBOM", "body": "sbom.json now lists exactly the pinned dependencies.",
                 "files": {"sbom.json": json.dumps(doc, indent=2) + "\n"}}
    else:
        patch = propose_patch(repo, target, status, key)
    if not patch["files"]:
        return None
    branch = f"standard/{area}/{item}/{uuid.uuid4().hex[:8]}"
    hardened = ("-c", "core.fsmonitor=false", "-c", "core.hooksPath=/dev/null", "-c", "core.sshCommand=false")
    git = lambda *a: subprocess.run(["git", *hardened, *a], cwd=repo, check=True, capture_output=True, text=True)
    git("checkout", "-B", branch, "origin/main")
    for path, content in patch["files"].items():
        full = allowed(repo, path, target)
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content)
    git("add", "--", *patch["files"])
    git("-c", "user.name=standard-agent", "-c", "user.email=agent@standard.invalid", "commit", "-m", patch["title"])
    git("push", "origin", branch)
    body = (f"{patch['body']}\n\n---\nStandard target `{target}` (`repo:{area}:{item}`) read `{status}`. "
            "This pull request merges only through the law: green CI and a dependency-only scope, or a human review.")
    return gh.open_pull(branch, patch["title"], body)
