"""IV-H G08/G16: focused invariant tracking for target:vulns and escalation semantics."""
import io,json,sys
from contextlib import redirect_stdout
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/"tests")]
from sim import Sim
from ops import lifecycle,cycle
from ops.cycle import TARGETS

def inspect():
    with redirect_stdout(io.StringIO()):
        with Sim({"vulns":"found:2"}) as sim:
            sim.default_test="found:1"
            frames=[]
            for i in range(8):
                sim.cycle(minutes=1500 if i in (3,6) else 1)
                n=sim.node()
                try:
                    s=n.state;now=n.now();health=n.journal.health(required_at=now)
                    matches={category:[x for x in health.get(category,[]) if isinstance(x,dict)
                                and (x.get("target")=="vulns" or x.get("obligation")=="target:vulns")]
                             for category in ("open","proven","escalated")}
                    subj=[{"resource":x.resource,"phase":lifecycle.phase(s,x,now,cycle.REVIEWERS)[0]}
                          for x in lifecycle.declared(s) if x.area=="deps" and x.item=="vulns"]
                    frames.append({"step":i+1,"now":now,"target_vulns":matches,
                         "proposals":subj,"gap_signal":sim.measured["vulns"],
                         "global_escalations":len(health.get("escalated",[])),
                         "global_open":len(health.get("open",[]))})
                finally:n.close()
    rows=[f["target_vulns"]["open"] for f in frames]
    identities=[[{k:r.get(k) for k in ("obligation","subject","opened","due","owner","needs")}
                  for r in rs] for rs in rows]
    return {"target_spec":TARGETS.get("vulns"),"timeline":frames,
         "persistent_same_open_identity":bool(identities[0]) and all(x==identities[0] for x in identities),
         "coverage_limit":"Observed one target on synthetic clock; no implication about universal closure or external truth.",
         "escalation_limit":"Zero global escalations before target due does not establish a missed mandatory escalation."}
def main():
    try:
        result={"id":"IVH-G08-G16-canonical-vulns","status":"OBSERVED","evidence":inspect()}
    except Exception as e:
        result={"id":"IVH-G08-G16-canonical-vulns","status":"INCONCLUSIVE",
                "evidence":{"error":type(e).__name__,"detail":str(e)[:350]}}
    print(json.dumps({"campaign":"IV-H","experiments":[result]},indent=2,default=str))
    return int(result["status"]=="INCONCLUSIVE")
if __name__=="__main__":raise SystemExit(main())
