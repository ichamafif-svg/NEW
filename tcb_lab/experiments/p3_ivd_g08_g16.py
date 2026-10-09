"""G08/G16 adversarial longitudinal experiment on a single real local git target.
Instrument both safety (no debt silently proven) and liveness (progress or escalation)
without equating ops proposal IDs with constitutional obligation identities.
"""
import io,json,sys
from contextlib import redirect_stdout
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/"tests")]
from sim import Sim
from ops import lifecycle

def run_scenario(name,steps,verdict,heal_at=None):
    with redirect_stdout(io.StringIO()):
        with Sim({"vulns":"none" if name=="G16-healthy-20" else "found:2"}) as sim:
            sim.default_test=verdict
            if name=="G16-healthy-20":
                sim.advisories={}  # eliminate simulated vulnerable package advisories too
            base=sim.world.main_head()
            trace=[];seen=set();first_obligations={};reset_candidates=[]
            for i in range(steps):
                if heal_at is not None and i==heal_at:
                    sim.measured["vulns"]="none"
                    sim.default_test="none"
                sim.cycle()
                node=sim.node()
                try:
                    st=node.state;now=node.now()
                    keys=sorted(str(k) for k in st.get("obligations",{}))
                    live=bool(lifecycle.live(st,now))
                    for k in keys:first_obligations.setdefault(k,i)
                finally:node.close()
                ph=sim.subjects();new=sorted(set(ph)-seen);seen.update(ph)
                trace.append({"step":i+1,"now":now,"gap_reported":sim.measured["vulns"],
                    "phases":dict(sorted(ph.items())),"new_subjects":new,"obligations":keys,
                    "live":live,"main_changed":sim.world.main_head()!=base})
            return {"scenario":name,"attempts":steps,"heal_at_cycle":heal_at+1 if heal_at is not None else None,
                "distinct_proposals":len(seen),"last":trace[-1],
                "live_cycles":sum(x["live"] for x in trace),
                "cycles_without_active_work_while_gap_reported":sum(
                    (not x["live"]) and x["gap_reported"]!="none" for x in trace),
                "obligation_keys_ever":sorted(first_obligations),
                "trace":trace,
                "control_configuration":{"initial_vulns": "none" if name=="G16-healthy-20" else "found:2","advisories_disabled":name=="G16-healthy-20"},
                "caveat":"Observed legacy ops proposal lifecycle. Stable constitutional debt identity and due timestamp are not asserted by this harness."}

def main():
    scenarios=[("G08-red-20",20,"found:1",None),
               ("G08-healed-20",20,"found:1",5),
               ("G16-red-20",20,"found:1",None),
               ("G16-healthy-20",20,"none",None)]
    rows=[]
    for name,cycles,verdict,heal_at in scenarios:
        try:
            rows.append({"id":name,"status":"OBSERVED",
                 "evidence":run_scenario(name,cycles,verdict,heal_at)})
        except Exception as e:
            rows.append({"id":name,"status":"INCONCLUSIVE",
                 "evidence":{"error":type(e).__name__,"message":str(e)[:300]}})
    print(json.dumps({"campaign":"IV-D","focus":"G08/G16","experiments":rows},indent=2))
    return int(any(x["status"]=="INCONCLUSIVE" for x in rows))
if __name__=="__main__":raise SystemExit(main())
