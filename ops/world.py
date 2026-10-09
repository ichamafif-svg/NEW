"""The world, as the untrusted roles may touch it: GitHub and PyPI, through typed questions about named subjects.

Principle (cause 1 of the M2 review): nothing is enumerated. No role lists pull requests, reviews or runs and decides
from whoever shows up. A role asks about a subject the journal already names (a commit SHA, a pull request the agent
declared, the head of main), and checks that the answer belongs to that subject (this repository, this SHA, base
main). What GitHub returns about anything else does not exist for Standard."""
from __future__ import annotations

import base64
import json
import re
import urllib.error
import urllib.parse
import urllib.request

SHA = re.compile(r"^[0-9a-f]{40}$")
NUMBER = re.compile(r"^[1-9][0-9]{0,9}$")


class WorldError(RuntimeError):
    pass


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

    def get(self, path, **params):
        return self.call("GET", path + ("?" + urllib.parse.urlencode(params) if params else ""))

    # ---- questions about named subjects ------------------------------------------------------------------------
    def main_head(self) -> str:
        sha = self.get("/branches/main")["commit"]["sha"]
        if not SHA.fullmatch(sha):
            raise WorldError("main has no commit")
        return sha

    def ci(self, sha: str, workflow=".github/workflows/ci.yml") -> str | None:
        """Conclusion of this repository's own CI workflow on this exact commit; None if it has not concluded."""
        runs = [r for r in self.get("/actions/runs", head_sha=sha, per_page=50).get("workflow_runs", [])
                if r["head_sha"] == sha and r.get("path") == workflow
                and (r.get("head_repository") or {}).get("full_name") == self.repo]
        done = [r for r in runs if r["status"] == "completed"]
        return max(done, key=lambda r: r["run_number"])["conclusion"] if done else None

    def pull(self, number: str) -> dict:
        """A declared pull request, reduced to what may be believed about it."""
        if not NUMBER.fullmatch(number):
            raise WorldError("not a pull request number")
        p = self.get(f"/pulls/{number}")
        return {"head": p["head"]["sha"], "base": p["base"]["ref"], "merged": p.get("merged") is True,
                "open": p["state"] == "open", "same_repo": (p["head"].get("repo") or {}).get("full_name") == self.repo,
                "changed": p.get("changed_files")}

    def files(self, number: str) -> list:
        out = []
        for page in range(1, 31):
            rows = self.get(f"/pulls/{number}/files", per_page=100, page=page)
            out += [f["filename"] for f in rows]
            if len(rows) < 100:
                break
        return out

    def rule_types(self, branch="main") -> set:
        return {r["type"] for r in self.get(f"/rules/branches/{branch}")}

    # ---- the agent's only write: a commit built from data, then a pull request -----------------------------------
    def propose(self, branch: str, files: dict, title: str, body: str) -> dict:
        """Create one commit on a new branch from main through the API. No working tree, no git process: what the
        model wrote stays data and is never executed or interpreted by a tool."""
        base = self.main_head()
        tree = self.get(f"/git/commits/{base}")["tree"]["sha"]
        entries = [{"path": path, "mode": "100644", "type": "blob",
                    "sha": self.call("POST", "/git/blobs", {"content": base64.b64encode(text.encode()).decode(),
                                                             "encoding": "base64"})["sha"]}
                   for path, text in sorted(files.items())]
        new_tree = self.call("POST", "/git/trees", {"base_tree": tree, "tree": entries})["sha"]
        commit = self.call("POST", "/git/commits", {"message": title, "tree": new_tree, "parents": [base]})["sha"]
        self.call("POST", "/git/refs", {"ref": f"refs/heads/{branch}", "sha": commit})
        pr = self.call("POST", "/pulls", {"head": branch, "base": "main", "title": title, "body": body})
        return {"number": str(pr["number"]), "head": commit}


def pypi(name: str) -> dict:
    with urllib.request.urlopen(f"https://pypi.org/pypi/{urllib.parse.quote(name)}/json", timeout=30) as r:
        return json.loads(r.read())["info"]
