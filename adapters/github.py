"""Trusted GitHub adapter for `remediate`: merge exactly the judged commit of one pull request, at most once.

Inside the TCB budget: a bug here can send a wrong effect. It therefore takes nothing from the agent but the judged
arguments, sends one request, and lets GitHub refuse any other commit through `sha`. Outcomes:
  ok       GitHub reports the pull request merged at this head (now, or already by an earlier attempt)
  failed   GitHub refused before merging (head moved, checks missing, conflict)
  unknown  anything else: the line requires an independent reconciliation."""
import json
import re
import urllib.error
import urllib.request

HEAD = re.compile(r"^[0-9a-f]{40}$")
METHODS = ("merge", "squash", "rebase")


class GitHub:
    def __init__(self, repo: str, token: str, api: str = "https://api.github.com", opener=None):
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo) or not token:
            raise ValueError("an owner/name repository and a token are required")
        self.base, self.token = f"{api}/repos/{repo}", token
        self.open = opener or (lambda *a, **k: urllib.request.urlopen(*a, **k))

    def _call(self, method, path, body=None):
        req = urllib.request.Request(self.base + path, method=method,
                                     data=None if body is None else json.dumps(body).encode(),
                                     headers={"Authorization": f"Bearer {self.token}",
                                              "Accept": "application/vnd.github+json",
                                              "X-GitHub-Api-Version": "2022-11-28"})
        try:
            with self.open(req, timeout=30) as r:
                return r.status, json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as e:
            return e.code, {}

    def _merged_at(self, pr, head) -> bool:
        status, pull = self._call("GET", f"/pulls/{pr}")
        return status == 200 and pull.get("merged") is True and pull.get("head", {}).get("sha") == head

    def remediate(self, resource, args, reservation_key):
        pr, head, method = args["pr"], args["head"], args["method"]
        if not pr.isdigit() or not HEAD.fullmatch(head) or method not in METHODS:
            return "failed"
        if self._merged_at(pr, head):
            return "ok"                                 # an earlier attempt already landed this exact commit
        status, _ = self._call("PUT", f"/pulls/{pr}/merge",
                               {"sha": head, "merge_method": method,
                                "commit_title": f"standard: remediate {resource.split('/pr/')[0]} (#{pr})",
                                "commit_message": f"reservation {reservation_key}"})
        if status == 200:
            return "ok"
        if status in (405, 409, 422):                   # not mergeable, head moved, invalid: GitHub merged nothing
            return "failed"
        return "unknown"

    def ports(self) -> dict:
        return {"remediate": self.remediate}
