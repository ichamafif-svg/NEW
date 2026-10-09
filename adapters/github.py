"""Trusted GitHub adapter for `remediate`: move main from the judged base to the judged head, fast-forward only.

Inside the TCB budget: a bug here can send a wrong effect. It takes nothing but the judged arguments and sends one
ref update with force=false, so main ends exactly on the judged commit or does not move. Only the guard may update
main (repository ruleset), so main cannot change between the read and the write but through this adapter.
Outcomes:
  ok       main is the judged head (now, or already by an earlier attempt)
  failed   nothing was sent, main is not the judged base, or GitHub refused the fast-forward: nothing moved
  unknown  anything else: the line requires an independent reconciliation."""
import json
import re
import urllib.error
import urllib.request

SHA = re.compile(r"^[0-9a-f]{40}$")


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

    def remediate(self, resource, args, reservation_key):
        base, head = args["base"], args["head"]
        if not SHA.fullmatch(base) or not SHA.fullmatch(head):
            return "failed"
        status, ref = self._call("GET", "/git/ref/heads/main")
        if status != 200:
            return "failed"                             # nothing was sent
        main = ref.get("object", {}).get("sha")
        if main == head:
            return "ok"                                 # an earlier attempt already moved main to this commit
        if main != base:
            return "failed"                             # the transition judged is no longer the one available
        status, _ = self._call("PATCH", "/git/refs/heads/main", {"sha": head, "force": False})
        if status == 200:
            return "ok"
        if status in (409, 422):                        # not a fast-forward, or refused by a rule: nothing moved
            return "failed"
        return "unknown"

    def ports(self) -> dict:
        return {"remediate": self.remediate}
