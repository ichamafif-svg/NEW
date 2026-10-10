"""Trusted GitHub adapter for `remediate`: atomic beforeOid on the exact base.

Inside the TCB budget: a bug here can send a wrong effect. It takes nothing but the judged arguments and sends one
GraphQL updateRefs supplies beforeOid and afterOid with force=false. The
repository must independently enforce guard-only writes and exact credentials.
Outcomes:
  ok       main is the judged head (now, or already by an earlier attempt)
  failed   nothing was sent because main is not the judged base
  unknown  a request was attempted but its result is not proven: readback required."""
import json
import re
import urllib.error
import urllib.request

SHA = re.compile(r"^[0-9a-f]{40}$")


class GitHub:
    def __init__(self, repo: str, token: str, api: str = "https://api.github.com", opener=None):
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo) or not token:
            raise ValueError("an owner/name repository and a token are required")
        self.base, self.api, self.token = f"{api}/repos/{repo}", api, token
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
        status, repository = self._call("GET", "")
        if status != 200 or not isinstance(repository.get("node_id"), str):
            return "failed"                             # no update was attempted
        query = "mutation($input:UpdateRefsInput!){updateRefs(input:$input){clientMutationId}}"
        body = {"query": query, "variables": {"input": {
            "repositoryId": repository["node_id"], "clientMutationId": reservation_key,
            "refUpdates": [{"name": "refs/heads/main", "beforeOid": base,
                            "afterOid": head, "force": False}]}}}
        req = urllib.request.Request(self.api + "/graphql", method="POST", data=json.dumps(body).encode(),
                                     headers={"Authorization": f"Bearer {self.token}",
                                              "Accept": "application/vnd.github+json",
                                              "Content-Type": "application/json"})
        try:
            with self.open(req, timeout=30) as response:
                reply = json.loads(response.read() or b"{}")
            if reply.get("errors") or not reply.get("data", {}).get("updateRefs"):
                return "unknown"                         # may have reached the provider
            return "ok"
        except Exception:
            return "unknown"                             # never infer definitive non-application

    def ports(self) -> dict:
        return {"remediate": self.remediate}
