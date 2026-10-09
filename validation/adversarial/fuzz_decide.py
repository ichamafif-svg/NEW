"""Fuzz: signed entries of every kind with one field replaced by a hostile value; any non-Refused exception is a bug."""
import sys, itertools, copy, random
import pathlib; _r = pathlib.Path(__file__).resolve().parents[2]; sys.path.insert(0, str(_r / "tests")); sys.path.insert(0, str(_r))
from fixture import World, T0, DAY, Refused
w = World()
gid, t = w.grant("agent", ["effect:merge", "observe", "certify:real", "evidence", "reconcile"], ["repo:*"], T0 + 1)
iid = w.add("intent", "agent", t, under=gid, op="merge", args={"pr": "1", "method": "m"})
s = w.journal.state
POOL = [None, True, False, -1, 0, 2**53, "", "x", "root", "*", "repo:pr:1", gid, iid, [], [1], [{}], ["root"], {}, {"a": 1},
        {"threshold": 2, "identities": {}}, {"pr": {"x": 1}, "method": "m"}, {"count": True, "window": 1}, [[]], ["*"]]
bases = {
 "grant": dict(holder="agent", actions=["effect:merge"], resources=["repo:*"], conditions=[], not_after=T0 + 9 * DAY),
 "delegate": dict(parent=gid, holder="agent", actions=["effect:merge"], resources=["repo:*"], conditions=[], not_after=T0 + 9 * DAY, budget={"count": 1, "window": 1}),
 "intent": dict(under=gid, op="merge", args={"pr": "1", "method": "m"}, retry_of=iid),
 "observation": dict(under=gid, resource="repo:pr:1", property="p", status="s", level="real"),
 "evidence": dict(under=gid, resource="repo:pr:1", subject=iid, level="real"),
 "reconciliation": dict(under=gid, intent=iid, result="applied"),
 "revoke": dict(grant=gid), "freeze": dict(scope="repo:*"), "flag": dict(intent=iid), "veto": dict(proposal=gid),
 "activate": dict(proposal=gid), "unfreeze": dict(scope="repo:*"), "heartbeat": dict(seen=1),
 "checkpoint": dict(size=1, head="sha256:" + "0" * 64), "token": dict(intent=iid, args_digest="sha256:" + "0" * 64),
 "reservation": dict(token=iid), "execution": dict(token=iid, result="ok"),
 "rotate": dict(root=w.root), "law": dict(release=w.law),
}
authors = ["agent", "alice", "guard", "sentinel", "w1"]
bad = 0; n = 0
for kind, base in bases.items():
    for field in list(base) + ["at", "id", "author", "extra"]:
        for v in POOL:
            body = dict(base)
            at = s["last_at"] + 1
            if field == "at": at_v = v
            else: at_v = at
            if field in ("at", "id", "author"):
                pass
            else:
                body[field] = v
            for author in authors:
                n += 1
                try:
                    e, _ = w.signed(kind, author, at_v if field == "at" else at, signers=[author, "bob"] if author != "bob" else None, state=s, **body)
                    if field == "id": 
                        import base64, json
                    w.kernel.decide(s, e)
                except Refused:
                    pass
                except Exception as exc:
                    bad += 1
                    if bad < 15: print("ESCAPED", kind, field, repr(v)[:40], author, type(exc).__name__, exc)
print("cases", n, "escaped", bad)
