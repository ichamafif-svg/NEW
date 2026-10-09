"""R3: the `open` predicate reads law-obligation instances with no provenance/independence filter. An agent opens the
instance with its own observation and then satisfies its own capability condition (the `observed` predicate on the
very same observation is correctly refused)."""
import sys, copy
import pathlib; _r = pathlib.Path(__file__).resolve().parents[2]; sys.path.insert(0, str(_r / "tests")); sys.path.insert(0, str(_r))
from fixture import World, T0, DAY, Refused, make_law

law = make_law()
law["obligations"] = [{"id": "change-window", "level": "refuse", "due_ms": DAY, "on_due": "lapse",
                       "open": [{"kind": "observation", "key": "resource", "where": {"property": "window"}}]}]
law["conditions"] = {"in-window": {"all": [{"open": ["change-window", "resource"]}]},
                     "seen-open": {"all": [{"observed": ["window", "open", "unknown"]}]}}
w = World(law=law)
g_obs, t = w.grant("agent", ["observe", "certify:unknown"], ["repo:pr:*"], T0 + 1)
g_open, t = w.grant("agent", ["effect:merge"], ["repo:pr:*"], t, conditions=["in-window"])
g_seen, t = w.grant("agent", ["effect:merge"], ["repo:pr:*"], t, conditions=["seen-open"])
args = {"pr": "42", "method": "squash"}
for name, g in (("in-window", g_open), ("seen-open", g_seen)):
    t += 1
    try:
        w.add("intent", "agent", t, under=g, op="merge", args=args); print(name, "before self-observation: ADMITTED")
    except Refused as r:
        print(name, "before self-observation:", r.code)
t += 1
w.add("observation", "agent", t, under=g_obs, resource="repo:pr:42", property="window", status="open", level="unknown")
print("agent self-observed; open law instances:", [k for k in w.state["obligations"] if k.startswith("change-window")])
for name, g in (("seen-open", g_seen), ("in-window", g_open)):
    t += 1
    try:
        w.add("intent", "agent", t, under=g, op="merge", args=args); print(name, "after self-observation: ADMITTED")
    except Refused as r:
        print(name, "after self-observation:", r.code, r.detail)
iid = [k for k, v in w.state["intents"].items() if v["under"] == g_open][0]
calls = []
g = w.guard(lambda *a: calls.append(a) or "ok")
g.issue(iid, w.state["last_at"] + 1)
g.redeem(w.state["token_of"][iid], w.state["last_at"] + 1)
print("dispatched through both judges:", calls)
