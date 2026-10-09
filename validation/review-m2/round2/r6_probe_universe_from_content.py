# F6: the measured repo decides the probe's universe: a NUL byte removes a file from `secrets`, a quoted key hides an
# unpinned action. Both read as a full-coverage PASS.
import subprocess, tempfile
from pathlib import Path
from ops import probes
d = Path(tempfile.mkdtemp())
(d / "settings.py").write_bytes(b"#\0\nAWS = 'AKIAABCDEFGHIJKLMNOP'\nAPI_KEY = 'abcdefghijklmnop1234'\n")
(d / "ok.py").write_text("x = 1\n")
(d / ".github/workflows").mkdir(parents=True)
(d / ".github/workflows/x.yml").write_text('jobs:\n  a:\n    steps:\n      - "uses": evil/action@main\n')
subprocess.run(["git", "init", "-q"], cwd=d); subprocess.run(["git", "add", "-A"], cwd=d)
m = probes.secrets(d); print("secrets universe", sorted(m.universe), "->", probes.verdict("none", m))
m = probes.actions(d); print("actions ->", probes.verdict("all", m))
