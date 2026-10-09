# F3: a declared PR whose CI is red stays "open" forever: no intent, no close, and the target never gets another repair.
from sim import Sim, HEAD
with Sim({"vulns": "found:1"}) as sim:
    sim.cycle()
    sim.world.runs[HEAD] = "failure"
    for _ in range(20):
        s = sim.cycle(minutes=360)
    print("days:", 20*6/24, "proposals:", sim.world.proposals, "intents:", len(s["intents"]),
          "PR7 open:", sim.world.pulls["7"]["open"])
