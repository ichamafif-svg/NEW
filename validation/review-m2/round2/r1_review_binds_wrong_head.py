# F1: `ops review --pr N` signs whatever commit the agent declared for PR N, not the commit the human looked at.
from sim import Sim, HEAD
from ops import lifecycle
from ops.cycle import observe
EVIL = "e" * 40
with Sim({"sast": "found:1"}) as sim:
    # compromised agent: PR 7 shows benign commit HEAD on GitHub; agent declares a *different* head EVIL for PR 7
    sim.world.pulls["7"] = {"head": HEAD, "base": "main", "merged": False, "open": True, "same_repo": True,
                            "files": ["app/service.py"]}
    sim.world.proposals = 1
    n = sim.node()
    try:
        observe(n, "agent", f"repo:code:sast/pr/7/{EVIL}", "proposed", "open", level="unknown")
    finally:
        n.close()
    sim.run("review", pr="7")                         # human inspected PR 7 at HEAD (benign) and approves "#7"
    # before the next scan, the agent force-pushes EVIL back onto PR 7; CI is green on EVIL (tests still pass)
    sim.world.pulls["7"]["head"] = EVIL; sim.world.runs[EVIL] = "success"
    s = sim.node().state
    print("review signed on:", [k for k in s["observations"] if k.endswith("|review|icham")])
    s = sim.cycle(minutes=400); s = sim.cycle()
    print("executed:", list(s["executed"].values()), "merged:", sim.world.pulls["7"]["merged"],
          "merged head:", sim.world.pulls["7"]["head"] == EVIL)
