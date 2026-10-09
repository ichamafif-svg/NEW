"""R2 (re-verify after 9ae917f): probes must not report a pass without evidence."""
import json
import subprocess
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from ops import scan

d = Path(tempfile.mkdtemp())
(d / "requirements.txt").write_text("flask==2.2.2\nwerkzeug==2.2.2\n")
fail = lambda cmd, cwd: SimpleNamespace(returncode=1, stdout="", stderr="ResolutionImpossible")
with patch.object(scan, "_run", fail):
    print("(a1) vulns, pip-audit crashes:", scan.vulns(d))
skipped = json.dumps({"dependencies": [{"name": "flask", "version": "2.2.2", "vulns": []},
                                       {"name": "werkzeug", "skip_reason": "not on PyPI"}]})
with patch.object(scan, "_run", lambda cmd, cwd: SimpleNamespace(returncode=0, stdout=skipped)):
    print("(a2) vulns, one dependency skipped:", scan.vulns(d))
(d / "requirements.txt").write_text("flask==2.2.2\nevil @ https://evil.example/x.whl\n")
try:
    print("(a3) vulns with URL requirement:", scan.vulns(d))
except Exception as exc:  # noqa: BLE001  (measure() turns this into error:<type>)
    print("(a3) vulns with URL requirement raised:", type(exc).__name__)

g = Path(tempfile.mkdtemp())
subprocess.run(["git", "init", "-q", str(g)], check=True)
(g / "config prod.py").write_text('API_KEY = "AKIAABCDEFGHIJKLMNOP"\n')
subprocess.run(["git", "-C", str(g), "add", "."], check=True)
print("(b) secrets with AWS key in 'config prod.py':", scan.secrets(g))


class GH:
    repo = "o/demo"

    def pulls(self):
        return [{"number": 9, "user": {"login": "standard-agent[bot]"}, "base": {"ref": "main"},
                 "head": {"ref": "standard/code/sast/0123abcd", "sha": "e" * 40, "repo": {"full_name": "o/demo"}}}]

    def pull(self, n):
        return {"changed_files": 1}

    def check_runs(self, sha):
        return [{"name": "test", "conclusion": "success"}]

    def files(self, n):
        return ["app/service.py"]

    def can_write(self, login):
        return login == "maintainer"

    def reviews(self, n):
        return [{"state": "APPROVED", "commit_id": "e" * 40, "user": {"login": "random-outsider"}},
                {"state": "APPROVED", "commit_id": "e" * 40, "user": {"login": "maintainer"}},
                {"state": "CHANGES_REQUESTED", "commit_id": "e" * 40, "user": {"login": "maintainer2"}}]


print("(c) pull facts:", [f[1:] for f in scan.pull_facts(GH(), "standard-agent[bot]")])
