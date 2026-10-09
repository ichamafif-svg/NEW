"""R2: a client law (quorum k, ordinary delay) declares a refuse-level obligation whose `gate` names veto / revoke /
freeze. Afterwards no single human can veto, revoke or freeze: FLOOR-0's restrict polarity is gone."""
import sys, copy
import pathlib; _r = pathlib.Path(__file__).resolve().parents[2]; sys.path.insert(0, str(_r / "tests")); sys.path.insert(0, str(_r))
from fixture import World, T0, DAY, Refused, make_law

w = World()
gid, t = w.grant("agent", ["effect:merge"], ["repo:pr:*"], T0 + 1)
law = copy.deepcopy(w.law)
law["obligations"] = [{"id": "brake-permit", "level": "refuse", "due_ms": DAY, "on_due": "lapse",
                       "open": [{"kind": "checkpoint", "key": "head", "where": {"size": -1}}],   # never opens
                       "gate": [{"kind": "veto", "key": "proposal"}, {"kind": "revoke", "key": "grant"},
                                {"kind": "freeze", "key": "scope"}, {"kind": "flag", "key": "intent"}]}]
_, t = w.widen("law", t, release=law)            # alice+bob, 1h delay, nobody vetoed in time
print("law with gated restrictions is in force")

def attempt(kind, author, **f):
    global t
    t += 1
    try:
        w.add(kind, author, t, **f); return "ADMITTED"
    except Refused as r:
        return f"{r.code}: {r.detail}"

print("revoke by carol :", attempt("revoke", "carol", grant=gid))
print("freeze by sentinel:", attempt("freeze", "sentinel", scope="repo:*"))
pid = w.add("grant", "alice", t + 1, ["alice", "bob"], holder="agent", actions=["effect:merge"],
            resources=["*"], conditions=[], not_after=T0 + 60 * DAY); t += 2
print("veto by carol    :", attempt("veto", "carol", proposal=pid))
iid = w.add("intent", "agent", t + 1, under=gid, op="merge", args={"pr": "1", "method": "m"}); t += 2
print("flag by sentinel :", attempt("flag", "sentinel", intent=iid))
