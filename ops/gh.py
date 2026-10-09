"""Minimal GitHub REST client for the untrusted layers (scanner, agent). No authority comes from it."""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request


class GitHubError(RuntimeError):
    pass


class Client:
    def __init__(self, repo: str, token: str, api: str = "https://api.github.com"):
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo or ""):
            raise ValueError("owner/name repository required")
        self.repo, self.token, self.api = repo, token, api

    def call(self, method, path, body=None, ok=(200, 201, 204)):
        url = path if path.startswith("http") else f"{self.api}/repos/{self.repo}{path}"
        req = urllib.request.Request(url, method=method, data=None if body is None else json.dumps(body).encode(),
                                     headers={"Authorization": f"Bearer {self.token}",
                                              "Accept": "application/vnd.github+json",
                                              "X-GitHub-Api-Version": "2022-11-28"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                data = r.read()
                return json.loads(data) if data else {}
        except urllib.error.HTTPError as e:
            if e.code in ok:
                return {}
            raise GitHubError(f"{method} {path}: HTTP {e.code} {e.read()[:300]!r}") from None

    def get(self, path, **params):
        return self.call("GET", path + ("?" + urllib.parse.urlencode(params) if params else ""))

    def pulls(self):
        return self.get("/pulls", state="open", per_page=100)

    def pull(self, number):
        return self.get(f"/pulls/{number}")

    def files(self, number):
        return [f["filename"] for f in self.get(f"/pulls/{number}/files", per_page=100)]

    def reviews(self, number):
        return self.get(f"/pulls/{number}/reviews", per_page=100)

    def check_runs(self, sha):
        return self.get(f"/commits/{sha}/check-runs", per_page=100).get("check_runs", [])

    def rules(self, branch):
        return self.get(f"/rules/branches/{branch}")

    def latest_run(self, workflow, branch):
        runs = self.get(f"/actions/workflows/{workflow}/runs", branch=branch, per_page=1).get("workflow_runs", [])
        return runs[0] if runs else None

    def open_pull(self, head, title, body, base="main"):
        return self.call("POST", "/pulls", {"head": head, "base": base, "title": title, "body": body})
