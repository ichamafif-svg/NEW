"""IV-F G08/G16 time discriminant: backoff vs indefinite abandonment.

Observe signed attempt timestamps, health open/escalated and next-planned work
before and after the operational 24h retry boundary. This cannot prove fairness.
"""
import io,json,sys
from contextlib import redirect_stdout
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/"tests")]
from sim import Sim
from ops import lifecycle,cycle

def probe(jump):
    with redirect_stdout(io.StringIO()):
        with Sim({"vulns":"found:2"}) as sim:
            sim.default_test="found:1"
            timeline=[]
            for step in range(5):
                sim.cycle(minutes=1500 if step==3 and jump else 1)
                node=sim.node()
                try:
                    st=node.state;now=node.now()
                    h=node.journal.health(required_at=now)
                    attempts=[{"resource":x["resource"],"status":x["status"],"at":x["at"]}
                         for x in st["observations"].values()
                         if x["author"]=="agent" and x["property"]=="attempt"]
                    timeline.append({"cycle":step+1,"now":now,
                        "subjects":sim.subjects(),
                        "plan":[{"verb":a.verb,"role":a.role} for a in lifecycle.plan(st,now,cycle.REVIEWERS)],
                        "attempts":attempts,
                        "open":len(h.get("open",[])),"escalated":len(h.get("escalated",[])),
                        "proven":len(h.get("proven",[]))})
                finally:node.close()
    return {"clock_jump_past_24h":jump,"trace":timeline,
            "interpretation":"No assumption that a new proposal must be admitted or health means proven physical truth"}

def main():
    rows=[]
    for flag in (False,True):
        try:rows.append({"id":"IVF-G16-"+("post24h" if flag else "minute-control"),
                         "status":"OBSERVED","evidence":probe(flag)})
        except Exception as e:rows.append({"id":"IVF-G16-"+("post24h" if flag else "minute-control"),
                         "status":"INCONCLUSIVE","evidence":{"type":type(e).__name__,"detail":str(e)[:300]}})
    print(json.dumps({"campaign":"IV-F","experiments":rows},indent=2))
    return int(any(x["status"]=="INCONCLUSIVE" for x in rows))
if __name__=="__main__":raise SystemExit(main())
