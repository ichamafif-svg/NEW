"""The world, as the untrusted roles may touch it: GitHub's git objects and PyPI, through typed questions about
named subjects.

Rule 1: nothing is enumerated. A role asks about a commit the journal names (a declared head, its base, main's head,
the anchor) and reads git objects, which are content-addressed: the answer is about that object or it is an error.
No pull request, review, check or run is consulted; the transition base -> head is the subject, and its content is
the full tree of each commit, not a projection of it."""
from __future__ import annotations

import base64
import json
import re
import urllib.error
import urllib.parse
import urllib.request

SHA = re.compile(r"^[0-9a-f]{40}$")


class WorldError(RuntimeError):
    pass


def sha(value) -> str:
    if not isinstance(value, str) or not SHA.fullmatch(value):
        raise WorldError("not a commit id")
    return value


class GitHub:
    def __init__(self, repo: str, token: str, api: str = "https://api.github.com"):
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo or ""):
            raise ValueError("owner/name repository required")
        self.repo, self.token, self.api = repo, token, api

    def call(self, method, path, body=None):
        url = path if path.startswith("http") else f"{self.api}/repos/{self.repo}{path}"
        req = urllib.request.Request(url, method=method, data=None if body is None else json.dumps(body).encode(),
                                     headers={"Authorization": f"Bearer {self.token}",
                                              "Accept": "application/vnd.github+json",
                                              "X-GitHub-Api-Version": "2022-11-28"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
                return json.loads(data) if data else {}
        except urllib.error.HTTPError as e:
            raise WorldError(f"{method} {path}: HTTP {e.code}") from None

    # ---- reading git objects ---------------------------------------------------------------------------------
    def main_head(self) -> str:
        return sha(self.call("GET", "/git/ref/heads/main")["object"]["sha"])

    def parents(self, commit: str) -> list:
        return [sha(p["sha"]) for p in self.call("GET", f"/git/commits/{sha(commit)}")["parents"]]

    def tree(self, commit: str) -> dict:
        """path -> blob id, the whole tree of the commit (a truncated listing is an error, never a partial answer)."""
        tree = self.call("GET", f"/git/commits/{sha(commit)}")["tree"]["sha"]
        listing = self.call("GET", f"/git/trees/{sha(tree)}?recursive=1")
        if listing.get("truncated"):
            raise WorldError("tree too large to be read whole")
        return {e["path"]: e["sha"] for e in listing["tree"] if e["type"] == "blob"}

    def blob(self, blob: str) -> bytes:
        data = self.call("GET", f"/git/blobs/{sha(blob)}")
        if data.get("encoding") != "base64":
            raise WorldError("unexpected blob encoding")
        return base64.b64decode(data["content"])

    def contains(self, ancestor: str, descendant: str) -> bool:
        """True if `ancestor` is in the history of `descendant`."""
        status = self.call("GET", f"/compare/{sha(ancestor)}...{sha(descendant)}")["status"]
        return status in ("identical", "ahead")

    def history(self, since: str, head: str, cap: int = 10_000) -> list:
        """First-parent commits after `since` up to `head`, oldest first. Walked by parent links, never listed."""
        out, at = [], sha(head)
        while at != since:
            if len(out) >= cap:
                raise WorldError("history longer than the cap")
            out.append(at)
            parents = self.parents(at)
            if not parents:
                raise WorldError("the anchor is not in main's history")
            at = parents[0]
        return out[::-1]

    def rule_types(self, branch="main") -> set:
        return {r["type"] for r in self.call("GET", f"/rules/branches/{branch}")}

    def tag_commit(self, owner_repo: str, tag: str) -> str:
        """The commit a tag of another repository points to (for pinning actions)."""
        ref = self.call("GET", f"{self.api}/repos/{owner_repo}/git/ref/tags/{urllib.parse.quote(tag)}")["object"]
        if ref["type"] == "tag":
            ref = self.call("GET", ref["url"])["object"]
        return sha(ref["sha"])

    # ---- the agent's only write: one child commit of main, built from data -----------------------------------
    def commit(self, base: str, files: dict, message: str) -> str:
        """Create a commit whose only parent is `base` and whose tree is base's with `files` replaced. No ref, no
        working tree, no git process: what the model wrote is data and nothing interprets it."""
        tree = self.call("GET", f"/git/commits/{sha(base)}")["tree"]["sha"]
        entries = [{"path": path, "mode": "100644", "type": "blob",
                    "sha": self.call("POST", "/git/blobs", {"content": base64.b64encode(data).decode(),
                                                             "encoding": "base64"})["sha"]}
                   for path, data in sorted(files.items())]
        new_tree = self.call("POST", "/git/trees", {"base_tree": tree, "tree": entries})["sha"]
        return sha(self.call("POST", "/git/commits", {"message": message, "tree": new_tree, "parents": [base]})["sha"])

    def keep(self, head: str):
        """Keep the proposed commit reachable under a ref no workflow listens to (not a branch, not a tag)."""
        self.call("POST", "/git/refs", {"ref": f"refs/standard/proposals/{sha(head)}", "sha": head})


def pypi(name: str) -> dict:
    with urllib.request.urlopen(f"https://pypi.org/pypi/{urllib.parse.quote(name)}/json", timeout=30) as r:
        return json.loads(r.read())["info"]
