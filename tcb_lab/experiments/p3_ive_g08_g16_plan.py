"""IV-E G08/G16: inspect why pending work is withdrawn or not replanned.

Observes the actual ops lifecycle.plan, latest scanner facts and canonical
obligation map. No inference of an escalation mechanism from absence in data.
"""
import io,json,sys
from contextlib import redirect_stdout
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/"tests")]
from sim import Sim
from ops import lifecycle,cycle

def experiment(label,red,steps):
    with redirect_stdout(io.StringIO()):
        with Sim({"vulns":"found:2" if red else "none"}) as sim:
            sim.default_test="found:1" if red else "none"
            if not red:sim.advisories={}
            base=sim.world.main_head()
            timeline=[]
            for n in range(steps):
                sim.cycle()
                node=sim.node()
                try:
                    st=node.state;now=node.now()
                    subjects=lifecycle.declared(st)
                    actions=lifecycle.plan(st,now,cycle.REVIEWERS)
                    details=[]
                    health=node.journal.health(required_at=now)
                    health_summary={k:len(health.get(k,[])) for k in ("open","escalated","proven")}
                    attempt_observations=[{"resource":o["resource"],"status":o["status"],"at":o["at"]} for o in st["observations"].values() if o["author"]=="agent" and o["property"]=="attempt"]
                    for x in subjects:
                        phase,intent,condition=lifecycle.phase(st,x,now,cycle.REVIEWERS)
                        f=lifecycle.facts(st,x)
                        mine=lifecycle.facts(st,x,("agent",)).get("proposed",("open",0))
                        details.append({"resource":x.resource,"target":f"{x.area}:{x.item}",
                          "phase":phase,"condition":condition,"intent":intent,
                          "agent_proposal":list(mine),"scanner_facts":{k:list(v) for k,v in f.items()}})
                    timeline.append({"cycle":n+1,"now":now,"gap_signal":sim.measured["vulns"],
                      "actions":[{"role":a.role,"verb":a.verb,"subject":a.subject.resource} for a in actions],
                      "subjects":details,"obligations":sorted(st.get("obligations",{})),
                      "accountability":health_summary,"attempt_facts":attempt_observations,
                      "main_changed":sim.world.main_head()!=base})
                finally:node.close()
    idle=[r["cycle"] for r in timeline if r["gap_signal"]!="none" and not r["actions"]]
    return {"scenario":label,"trace":timeline,"no_plan_while_gap":idle,
       "no_plan_count":len(idle),"proposals":len(timeline[-1]["subjects"]),
       "observability":"Plan actions != executed effects; accountability health includes open and escalated but their target linkage must be checked."}

def main():
    out=[]
    for label,red in (("G08-gap-reasons",True),("G16-healthy-reasons",False)):
        try:out.append({"id":"IVE-"+label,"status":"OBSERVED",
                        "evidence":experiment(label,red,8)})
        except Exception as exc:out.append({"id":"IVE-"+label,"status":"INCONCLUSIVE",
                           "evidence":{"type":type(exc).__name__,"detail":str(exc)[:250]}})
    print(json.dumps({"campaign":"IV-E","experiments":out},indent=2))
    return int(any(x["status"]=="INCONCLUSIVE" for x in out))
if __name__=="__main__":raise SystemExit(main())
