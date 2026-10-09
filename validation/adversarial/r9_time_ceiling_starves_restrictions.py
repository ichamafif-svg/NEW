"""R9: any identity that can get one entry admitted may stamp it at anchor_at + MAX_AHEAD_MS. Until the next witness
checkpoint, no other entry (freeze, revoke, veto...) has any admissible timestamp. Right after each checkpoint the same
identity can re-saturate the ceiling with one cheap entry (here a self-delegation)."""
import sys
import pathlib; _r = pathlib.Path(__file__).resolve().parents[2]; sys.path.insert(0, str(_r / "tests")); sys.path.insert(0, str(_r))
from fixture import World, T0, DAY, Refused, MAX_AHEAD_MS

w = World()
gid, t = w.grant("agent", ["effect:merge"], ["repo:pr:*"], T0 + 1)
def saturate():
    s = w.state
    ceiling = s["anchor_at"] + MAX_AHEAD_MS
    w.add("delegate", "agent", ceiling, parent=gid, holder="agent", actions=["effect:merge"],
          resources=["repo:pr:1"], conditions=[], not_after=ceiling + 1)
    return ceiling
for rnd in range(3):
    c = saturate()
    for kind, author, f in (("freeze", "sentinel", {"scope": "repo:*"}), ("revoke", "carol", {"grant": gid})):
        out = []
        for at in (c, c + 1):
            try:
                w.add(kind, author, at, **f); out.append("ADMITTED")
            except Refused as r:
                out.append(r.code)
        print("round", rnd, kind, "at ceiling ->", out[0], "; at ceiling+1 ->", out[1])
    w.tick(c + 60_000)                                 # witnesses checkpoint; the agent immediately saturates again
