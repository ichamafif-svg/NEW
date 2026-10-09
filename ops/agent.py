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


def propose_patch(repo: Path, target: str, status: str, key: str) -> dict:
    prompt = (f"Repository files follow. The maintenance target `{target}` currently reads `{status}`.\n"
              f"Task: {GUIDE[target]}\nReturn JSON: {{\"title\": str, \"body\": str, \"files\": "
              f"{{path: full new content}}}}. Change as few files as possible. Never touch .github/ except for the "
              f"`actions` target.\n\n{context(repo)}")
    patch = claude(prompt, key)
    files = patch.get("files") or {}
    for path in files:
        rel = Path(path)
        if rel.is_absolute() or ".." in rel.parts or (FORBIDDEN.match(path) and not
                                                       (target == "actions" and path.startswith(".github/workflows/"))):
            raise ValueError(f"the agent may not write {path}")
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
    git = lambda *a: subprocess.run(["git", *a], cwd=repo, check=True, capture_output=True, text=True)
    git("checkout", "-B", branch, "origin/main")
    for path, content in patch["files"].items():
        (repo / path).parent.mkdir(parents=True, exist_ok=True)
        (repo / path).write_text(content)
    git("add", "--", *patch["files"])
    git("-c", "user.name=standard-agent", "-c", "user.email=agent@standard.invalid", "commit", "-m", patch["title"])
    git("push", "origin", branch)
    body = (f"{patch['body']}\n\n---\nStandard target `{target}` (`repo:{area}:{item}`) read `{status}`. "
            "This pull request merges only through the law: green CI and a dependency-only scope, or a human review.")
    return gh.open_pull(branch, patch["title"], body)
