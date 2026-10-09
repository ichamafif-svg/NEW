"""R5 re-verify: (1) direct .git/config is refused; (2) a tracked symlink inside the work tree that points into .git
passes allowed(): the is_symlink() test runs on the *resolved* path, so it is always False."""
import subprocess
import tempfile
from pathlib import Path

from ops import agent

repo = Path(tempfile.mkdtemp()) / "repo"
subprocess.run(["git", "init", "-q", str(repo)], check=True)
(repo / "meta").symlink_to(".git")                      # e.g. a symlink that once landed on main
for p in (".git/config", "meta/config", "meta/info/attributes"):
    try:
        print(p, "->", agent.allowed(repo, p, "sast"))
    except ValueError as exc:
        print(p, "-> refused:", exc)
