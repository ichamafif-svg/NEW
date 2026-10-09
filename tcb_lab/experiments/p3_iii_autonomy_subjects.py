"""P3 campaign III — conditional autonomy replay with full subject transitions.

This instrument does not interpret a live replacement as good or bad.
It records exact resource identity, phase, clock, and old/new subjects.
"""
import io,json,sys
from contextlib import redirect_stdout
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/"tests")]
from sim import Sim
from ops import lifecycle

def experiment(label,verdict,ncycles):
    with Sim({"vulns":"found:2"}) as sim:
        sim.default_test=verdict
        base=sim.world.main_head()
        timeline=[]
        for cycle in range(ncycles):
            with redirect_stdout(io.StringIO()):
                sim.cycle()
            node=sim.node()
            try:
                now=node.now()
                live=bool(lifecycle.live(node.state,now))
            finally:node.close()
            subjects=sim.subjects()
            timeline.append({"cycle":cycle+1,"now":now,"main_unchanged":sim.world.main_head()==base,
                "subjects":dict(sorted(subjects.items())),"live":live,
                "count_withdrawn":sum(v=="withdrawn" for v in subjects.values()),
                "count_measuring":sum(v=="measuring" for v in subjects.values())})
        last=timeline[-1]
        return {"variant":label,"verdict":verdict,"cycles":timeline,
            "historic_no_live":not last["live"],"new_subject_after_withdrawn":any(
                x["count_measuring"]>0 and x["count_withdrawn"]>0 for x in timeline),
            "limit":"fresh Sim on each run, local CI fixture; source of time nondeterminism not isolated"}

def quiet_experiment(*args):
    with redirect_stdout(io.StringIO()):
        return experiment(*args)

def main():
    rows=[]
    for verdict in ("found:1","none"):
        for count in (2,3,5):
            for rep in range(3):
                ident="P3-III-O-"+verdict+"-"+str(count)+"-"+str(rep)
                try:rows.append({"id":ident,"status":"OBSERVED",
                                 "evidence":quiet_experiment(ident,verdict,count)})
                except Exception as e:rows.append({"id":ident,"status":"INCONCLUSIVE",
                   "evidence":{"error":type(e).__name__,"detail":str(e)[:260]}})
    print(json.dumps({"campaign":"III","branch":"O/R","experiments":rows},indent=2))
    return int(any(x["status"]=="INCONCLUSIVE" for x in rows))
if __name__=="__main__":raise SystemExit(main())
