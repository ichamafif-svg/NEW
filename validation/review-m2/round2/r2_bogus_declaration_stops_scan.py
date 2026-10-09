# F2: one declaration the world cannot answer kills the whole scan role, every run (and with `needs:`, agent+guard).
from sim import Sim
from ops.cycle import observe
from ops.world import GitHub
with Sim({"vulns": "found:1"}) as sim:
    n = sim.node()
    try:
        observe(n, "agent", "repo:deps:vulns/pr/abc/zzz", "proposed", "open", level="unknown")
    finally:
        n.close()
    # the simulated world mirrors ops.world: unknown number -> exception (real GitHub: WorldError on NUMBER / 404)
    for i in range(3):
        sim.clock.t += 400 * 60
        try:
            sim.run("scan"); print("scan", i, "ok")
        except Exception as e:
            print("scan", i, "CRASH", type(e).__name__, e)
    try:
        GitHub("o/r", "t").pull("abc")
    except Exception as e:
        print("real ops.world.pull('abc') ->", type(e).__name__, e)
