"""IV-I G16 deadline crossing: compare just-before and just-after target:vulns due.

The oracle separates an overdue open obligation from a recorded escalation;
it does not assume overdue automatically requires an escalation unless specified.
"""
import io,json,sys
from contextlib import redirect_stdout
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/"tests")]
from sim import Sim
from ops import lifecycle,cycle

def sample(after):
    with redirect_stdout(io.StringIO()):
        with Sim({"vulns":"found:2"}) as sim:
            sim.default_test="found:1"
            sim.cycle()
            n=sim.node()
            try:
                h=n.journal.health(required_at=n.now())
                row=next(x for x in h.get("open",[]) if x.get("obligation")=="target:vulns")
                due=int(row["due"]);initial=int(n.now())
            finally:n.close()
            # One-minute cycle advances 60000ms. Stop 1ms before or 1ms after due.
            sim.clock.t+=(due-initial-60000+ (1 if after else -1))/1000
            sim.cycle()
            n=sim.node()
            try:
                now=n.now();h=n.journal.health(required_at=now)
                groups={k:[x for x in h.get(k,[]) if isinstance(x,dict) and x.get("obligation")=="target:vulns"]
                        for k in ("open","escalated","proven")}
                return {"after_due":after,"initial":initial,"due":due,"now":now,"delta_due_ms":now-due,
                    "target":groups,"total_escalations":len(h.get("escalated",[])),
                    "live":len(lifecycle.live(n.state,now,cycle.REVIEWERS)),
                    "planned":[{"role":a.role,"verb":a.verb} for a in lifecycle.plan(n.state,now,cycle.REVIEWERS)],
                    "gap_signal":sim.measured["vulns"]}
            finally:n.close()

def main():
    cases=[]
    for after in (False,True):
        ident="IVI-G16-"+("after-due" if after else "before-due")
        try:
            cases.append({"id":ident,"status":"OBSERVED","evidence":sample(after)})
        except Exception as ex:
            cases.append({"id":ident,"status":"INCONCLUSIVE",
                          "evidence":{"error":type(ex).__name__,"detail":str(ex)[:300]}})
    print(json.dumps({"campaign":"IV-I","experiments":cases},indent=2))
    return int(any(c["status"]=="INCONCLUSIVE" for c in cases))
if __name__=="__main__":raise SystemExit(main())
