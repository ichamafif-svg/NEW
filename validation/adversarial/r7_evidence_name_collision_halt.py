"""R7: invariants dispatches on getattr(self, '_' + kind). A law evidence kind named like a private method
(use, quorum, signed, profile, authority, proposal, obligations, law_entry, is_law) makes the second judge call that
method with the wrong arguments -> exception -> persistent halt on the first such attestation."""
import sys
import pathlib; _r = pathlib.Path(__file__).resolve().parents[2]; sys.path.insert(0, str(_r / "tests")); sys.path.insert(0, str(_r))
from fixture import World, T0, Refused, make_law

law = make_law()
law["evidence"] = {"quorum": {"fields": {"under": "id", "resource": "resource"}}}
w = World(law=law)
gid, t = w.grant("readback", ["quorum"], ["repo:*"], T0 + 1)
try:
    w.add("quorum", "readback", t, under=gid, resource="repo:pr:1")
except Refused as r:
    print(r.code, r.detail)
print("halted:", w.pins.halted())
