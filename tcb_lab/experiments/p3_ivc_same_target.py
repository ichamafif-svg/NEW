"""IV-C: one persistent degraded target, long-horizon progress/retry observations.

This is an ops-level diagnostic. It records subject IDs and phase changes;
it does not pretend that a subject ID is equivalent to constitutional debt.
"""
import io,json,sys
from contextlib import redirect_stdout
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/"tests")]
from sim import Sim
from ops import lifecycle

def investigate(verdict,cycles):
    with redirect_stdout(io.StringIO()):
        with Sim({"vulns":"found:2"}) as sim:
            sim.default_test=verdict
            baseline=sim.world.main_head()
            subjects_seen=set();sequence=[];previous={}
            for step in range(cycles):
                sim.cycle()
                node=sim.node()
                try:
                    now=node.now();state=node.state
                    live=bool(lifecycle.live(state,now))
                    obligation_keys=sorted(str(k) for k in state.get("obligations",{}))
                finally:node.close()
                current=sim.subjects()
                newborn=sorted(set(current)-set(previous))
                subjects_seen.update(current)
                sequence.append({"cycle":step+1,"subjects":dict(sorted(current.items())),
                  "born":newborn,"live":live,"at":now,
                  "obligation_keys":obligation_keys,
                  "main_changed":sim.world.main_head()!=baseline})
                previous=current
    return {"scenario":verdict,"cycles":cycles,"unique_subjects":len(subjects_seen),
      "timeline":sequence,"consecutive_active_after_withdrawal":sum(
      1 for x in sequence if "withdrawn" in x["subjects"].values() and x["live"]),
      "interpretation_limit":"legacy ops subject is not proof of persistent constitutional obligation"}

def main():
    cases=[]
    for verdict,cycles in (("found:1",12),("none",12)):
        case_id=f"IVC-OR-{verdict}-{cycles}"
        try:cases.append({"id":case_id,"status":"OBSERVED",
            "evidence":investigate(verdict,cycles)})
        except Exception as exc:cases.append({"id":case_id,"status":"INCONCLUSIVE",
           "evidence":{"error":type(exc).__name__,"detail":str(exc)[:250]}})
    print(json.dumps({"campaign":"IV-C","branch":"O/R","experiments":cases},indent=2))
    return int(any(x["status"]=="INCONCLUSIVE" for x in cases))
if __name__=="__main__":raise SystemExit(main())
