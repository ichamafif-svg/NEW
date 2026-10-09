"""R4: one transient merge refusal (405: base modified / conflict after a sibling merge, 409, 422) stalls the target
forever: `ask` never re-asks a (pr, head) it asked once, and `repair` never opens a new PR while one is open for the
item. Same for `unknown` (502/timeout): ops/ never reconciles, so no retry and no proof."""
import json
from pathlib import Path
from unittest.mock import patch

from harness import World, GOOD

HEAD = "a" * 40


class GH:
    repo = "o/demo"

    def can_write(self, login):
        return False

    def __init__(self):
        self.merged, self.opened = set(), 0

    def pulls(self):
        return [] if "7" in self.merged else [
            {"number": 7, "user": {"login": "standard-agent[bot]"}, "base": {"ref": "main"},
             "head": {"ref": "standard/deps/vulns/abcd1234", "sha": HEAD, "repo": {"full_name": "o/demo"}}}]

    def pull(self, n):
        return {"merged": str(n) in self.merged, "head": {"sha": HEAD}, "changed_files": 1}

    def merge(self, n):
        self.merged.add(str(n))

    def files(self, n):
        return ["requirements.txt"]

    def reviews(self, n):
        return []

    def check_runs(self, sha):
        return [{"name": "test", "conclusion": "success"}]


gh = GH()
w = World(gh, measured=dict(GOOD, vulns="found:1"))
with w.env(), patch("ops.agent.open_repair", lambda *a: (setattr(gh, "opened", gh.opened + 1), {"number": 8})[1]):
    w.boot()
    w.clock.t += 60
    w.step("scan")
    w.step("ask")
    w.merge_status = 405                      # e.g. "Base branch was modified" right after a sibling PR merged
    s = w.step("guard")
    print("cycle 1 executed:", list(s["executed"].values()))
    w.merge_status = 200                      # GitHub would now accept the very same commit
    hp = Path(w.tmp) / "health.json"
    hp.write_text(json.dumps({"open": [{"type": "target", "target": "vulns", "due": 1}], "escalated": []}))
    for cycle_no in range(2, 6):
        w.clock.t += 6 * 3600
        w.step("scan")
        s = w.step("ask")
        w.step("guard")
        w.step("repair", health=str(hp))
    print("after 4 more cycles: intents", len(s["intents"]), "merged", sorted(gh.merged), "new repair PRs", gh.opened)
