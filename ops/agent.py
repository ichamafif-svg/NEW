"""The maintenance agent's craft: turn a measured gap into one commit, as data.

Principle (cause 3 of the M2 review): what the model writes is hostile data. It never reaches a working tree, a git
process or a shell: the commit is built through the GitHub API (world.commit) from a map {path: text} whose paths
must belong to the target's declared write scope. Whether the commit may then be merged is not decided here but by
the law, from facts an independent scanner observes about that exact commit."""
from __future__ import annotations

import json
import os
import re
import urllib.request
from pathlib import Path

from . import probes

API = "https://api.anthropic.com/v1/messages"
MODEL = os.environ.get("STANDARD_AGENT_MODEL", "claude-sonnet-5-5")
SEGMENT = r"[A-Za-z0-9_][A-Za-z0-9_.-]{0,99}"
SOURCE = rf"(?!tests/)(?!requirements)({SEGMENT}/){{0,8}}{SEGMENT}\.(py|md)"
DEPENDENCIES = r"requirements[A-Za-z0-9_.-]*\.txt|sbom\.json"
# target -> paths a repair of it may write. Nothing else is ever proposed, whatever the model answers.
WRITE_SCOPE = {
    "vulns": DEPENDENCIES, "licenses": DEPENDENCIES, "sbom": r"sbom\.json",
    "deps-age": rf"{DEPENDENCIES}|{SOURCE}",
    "secrets": SOURCE, "sast": SOURCE, "ci": SOURCE,
    "actions": rf"\.github/workflows/{SEGMENT}\.ya?ml",
}
TASK = {
    "vulns": "Upgrade the vulnerable pinned dependencies in requirements.txt to the lowest fixed versions; keep it a "
             "full lock of exact pins.",
    "deps-age": "Upgrade the pinned dependencies that are a major version behind, adapting the code if needed.",
    "licenses": "Replace dependencies whose license is not permissive.",
    "secrets": "Remove the hard-coded secret and read it from an environment variable instead.",
    "sast": "Fix the high-severity issues reported by bandit without changing behaviour.",
    "ci": "Make the failing test suite pass by fixing the code, never by weakening tests.",
    "actions": "Pin every GitHub Action to a full commit SHA, with the version in a comment.",
}


def in_scope(target: str, path) -> bool:
    return isinstance(path, str) and re.fullmatch(WRITE_SCOPE[target], path) is not None


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
    tree = probes.Checkout(repo)
    for p in sorted(tree.paths()):
        if not p.endswith((".py", ".md", ".txt", ".toml", ".yml", ".yaml", ".json")):
            continue
        try:
            raw = tree.read(p)
        except (OSError, FileNotFoundError):
            continue
        if (len(raw) > probes.MAX_FILE or b"\x00" in raw
                or any(pattern.search(raw) for pattern in probes.SECRETS)):
            continue  # detected secrets never leave in the model context
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            continue
        if size + len(text) > limit:
            break
        parts.append(f"=== {p} ===\n{text}")
        size += len(text)
    return "\n".join(parts)


def craft(repo: Path, target: str, status: str, key: str, *, constitution=None) -> dict:
    """{title, body, files} for one repair that needs judgment; files are checked against the write scope before
    anything leaves. Deterministic repairs are recipes (ops/recipes.py), not crafts."""
    if constitution is not None and not isinstance(constitution, str):
        raise ValueError("an agent requires contextual constitutional text")
    legal_context = ("\n" + constitution + "\n") if constitution is not None else ""
    reply = claude(f"Repository files follow. Maintenance target `{target}` reads `{status}`.\nTask: {TASK[target]}"
                   + legal_context
                   + f"\nReturn JSON {{\"title\": str, \"body\": str, \"files\": {{path: full new content}}}}, "
                   f"changing as few files as possible.\n\n{context(repo)}", key)
    files = reply.get("files") if isinstance(reply, dict) else None
    if (not isinstance(files, dict) or not files
            or not all(in_scope(target, p) and isinstance(t, str) for p, t in files.items())):
        raise ValueError(f"the repair of {target} leaves its write scope")
    return {"title": str(reply.get("title", ""))[:200] or f"Remediate {target}",
            "body": str(reply.get("body", ""))[:4000], "files": files}
