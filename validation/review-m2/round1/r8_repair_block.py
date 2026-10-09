"""R8 (missed by the V1 fix): cmd_repair's open_targets lists every open PR whose ref starts with 'standard/',
whatever its author or repository. (a) an outsider's fork PR `standard/deps/vulns/x` blocks the vulns repair
forever; (b) a fork PR `standard/x` makes split('/')[2] raise: no repair at all."""
import json
from pathlib import Path
from unittest.mock import patch

from harness import World, GOOD


class GH:
    repo = "o/demo"
    refs = []

    def pulls(self):
        return [{"number": 50 + i, "user": {"login": "mallory"}, "base": {"ref": "main"},
                 "head": {"ref": r, "sha": "0" * 40, "repo": {"full_name": "mallory/demo"}}} for i, r in enumerate(self.refs)]


gh, opened = GH(), []
w = World(gh, measured=dict(GOOD, vulns="found:1"))
hp = Path(w.tmp) / "health.json"
hp.write_text(json.dumps({"open": [{"type": "target", "target": "vulns", "due": 1}], "escalated": []}))
with w.env(), patch("ops.agent.open_repair", lambda *a: (opened.append(a[3:5]), {"number": 8})[1]):
    w.boot()
    w.clock.t += 60
    w.step("scan")
    for refs in ([], ["standard/deps/vulns/evil"], ["standard/x"]):
        gh.refs, opened[:] = refs, []
        try:
            w.step("repair", health=str(hp))
            print(refs, "-> repairs opened:", opened)
        except Exception as exc:  # noqa: BLE001
            print(refs, "-> repair crashed:", type(exc).__name__, exc)
