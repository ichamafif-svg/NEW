"""IV-G G08/G16: identify health open rows, stable identities and escalation under repeated failures.

Observational research only: reports qualified health entries and backoff/retry
trajectories. Distinguish target-level health obligations from effect-proof debt.
"""
import io,json,sys
from contextlib import redirect_stdout
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/"tests")]
from sim import Sim
from ops import lifecycle,cycle

def inspect(jump):
    with redirect_stdout(io.StringIO()):
        with Sim({"vulns":"found:2"}) as sim:
            sim.default_test="found:1"
            timeline=[]
            for i in range(7):
                sim.cycle(minutes=1500 if jump and i in (3,5) else 1)
                n=sim.node()
                try:
                    now=n.now();s=n.state;h=n.journal.health(required_at=now)
                    opens=h.get("open",[]);escalated=h.get("escalated",[])
                    if i==0:
                        samples={"open":[str(v)[:600] for v in opens[:25]],
                         "escalated":[str(v)[:600] for v in escalated[:25]]}
                    attempts=[{"resource":o["resource"],"status":o["status"],"at":o["at"]}
                        for o in s["observations"].values()
                        if o["author"]=="agent" and o["property"]=="attempt"]
                    timeline.append({"cycle":i+1,"now":now,"open":len(opens),
                        "escalated":len(escalated),"proven":len(h.get("proven",[])),
                        "open_fingerprints":sorted(str(v)[:250] for v in opens),
                        "escalated_fingerprints":sorted(str(v)[:250] for v in escalated),
                        "obligation_keys":sorted(s.get("obligations",{})),
                        "attempts":attempts,"live":len(lifecycle.live(s,now,cycle.REVIEWERS)),
                        "planned":[{"role":a.role,"verb":a.verb} for a in lifecycle.plan(s,now,cycle.REVIEWERS)]})
                finally:n.close()
    return {"two_25h_jumps":jump,"health_samples":samples,"timeline":timeline,
      "warning":"Health open rows are not assumed to be effect-proof debts; absence of escalation in seven cycles does not refute unbounded liveness."}
def main():
    rows=[]
    for jump in (False,True):
        name="IVG-G08-G16-"+("48h" if jump else "minute-control")
        try:rows.append({"id":name,"status":"OBSERVED","evidence":inspect(jump)})
        except Exception as e:rows.append({"id":name,"status":"INCONCLUSIVE",
            "evidence":{"error":type(e).__name__,"detail":str(e)[:300]}})
    print(json.dumps({"campaign":"IV-G","experiments":rows},indent=2))
    return int(any(x["status"]=="INCONCLUSIVE" for x in rows))
if __name__=="__main__":raise SystemExit(main())
