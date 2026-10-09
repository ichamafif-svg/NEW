"""R10: the DSSE envelope and its signature objects are not closed shapes. Unsigned extra fields (and duplicated
signatures) are admitted and stored, so any relay can change the entry bytes / head without any signer."""
import sys, copy
import pathlib; _r = pathlib.Path(__file__).resolve().parents[2]; sys.path.insert(0, str(_r / "tests")); sys.path.insert(0, str(_r))
from fixture import World, T0
w = World()
e, _ = w.signed("freeze", "sentinel", T0 + 1, scope="repo:*")
e2 = copy.deepcopy(e)
e2["envelope"]["unsigned_note"] = "x" * 1000
e2["envelope"]["signatures"].append(dict(e2["envelope"]["signatures"][0], extra="junk"))
print(w.kernel.admit(w.journal.state, e), w.kernel.admit(w.journal.state, e2))
w.journal.append(e2)
print("admitted mutated entry; head differs from the original:", w.state["head"])
