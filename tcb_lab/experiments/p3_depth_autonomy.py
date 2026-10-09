"""Phase 3: repeated historical maintenance scenarios at fixed source SHA.

Record outcomes without assuming that the test's expected no-live outcome
must always hold, and distinguish deterministic replay from changed timing.
"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/"tests")]
from sim import Sim
from ops import lifecycle

def experiment(verdict,cycles,repeat):
    with Sim({"vulns":"found:2"}) as sim:
        base=sim.world.main_head()
        sim.default_test=verdict
        trace=[]
        for step in range(cycles):
            with redirect_stdout(io.StringIO()):
                sim.cycle()
            n=sim.node()
            try: live=bool(lifecycle.live(n.state,n.now()))
            finally:n.close()
            subjects=sim.subjects()
            trace.append({"step":step+1,"phases":sorted(subjects.values()),
                          "live":live,"head_changed":sim.world.main_head()!=base,
                          "subjects":len(subjects)})
        return {"repeat":repeat,"verdict":verdict,"cycles":cycles,
                "final":trace[-1],"phase_trace":trace,
                "historical_expectation":cycles==2 and verdict=="found:1",
                "historic_assertions_hold":(sum(p=="withdrawn" for p in trace[-1]["phases"])==1
                and not trace[-1]["head_changed"] and not trace[-1]["live"]) if cycles==2 and verdict=="found:1" else None}
def main():
    rows=[]
    variants=[("red_two", "found:1",2,10),("red_three","found:1",3,3),
              ("clean_two","none",2,3)]
    for name,verdict,cycles,count in variants:
        for n in range(count):
            ident=f"P3-O2-{name}-{n+1}"
            try:rows.append({"id":ident,"status":"OBSERVED","evidence":experiment(verdict,cycles,n)})
            except Exception as exc:rows.append({"id":ident,"status":"INCONCLUSIVE","evidence":{"error":type(exc).__name__,"detail":str(exc)[:220]}})
    print(json.dumps({"priority":"O1/R1","experiments":rows},indent=2))
    return int(any(x["status"]=="INCONCLUSIVE" for x in rows))
if __name__=="__main__":raise SystemExit(main())
