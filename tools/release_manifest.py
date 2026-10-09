"""Produce the code identity to review; generation is not human approval."""
import hashlib
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
import bootstrap

value = bootstrap.manifest(root)
raw = bootstrap.encoded(value)
(root / 'tcb-release.json').write_bytes(raw)
print('sha256:' + hashlib.sha256(raw).hexdigest())
