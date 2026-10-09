"""Phase 3 depth: provider post-send ambiguity, repeated redemption and independent journal."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/"tests")]
from fixture import World,T0
from tcb.kernel import Refused

def experiment(response,alternative_journal=False):
    w=World()
    grant,t=w.grant("agent",["effect:merge"],["repo:pr:*"],T0+1)
    iid=w.add("intent","agent",t,under=grant,op="merge",args={"pr":"42","method":"squash"})
    effects=[]
    def execute(*a):
        effects.append({"action":a[0]})
        if response=="ack_lost":raise OSError("synthetic post-application ACK loss")
        return response
    g=w.guard(execute)
    g.issue(iid,t+1)
    token=w.state["token_of"][iid]
    g.redeem(token,t+2)
    first_state=w.state["executed"][token]
    contender=w.guard(execute,journal=w.other_journal()) if alternative_journal else g
    try:contender.redeem(token,t+3);second="ADMITTED"
    except Refused as exc:second=exc.code
    return {"response":response,"alternative_journal":alternative_journal,
            "synthetic_effect_calls":len(effects),"stored_outcome":first_state,
            "repeat_redemption":second,"obligations":sorted(k for k in w.state["obligations"] if iid in k),
            "physical_limit":"single SQLite file, no separate host/provider"}
def main():
    rows=[]
    for response in ("ack_lost","unknown","ok","failed"):
        for alt in (False,True):
            name=f"P3-E2-{response}-"+("other_journal" if alt else "same_guard")
            try:rows.append({"id":name,"status":"OBSERVED","evidence":experiment(response,alt)})
            except Exception as e:rows.append({"id":name,"status":"INCONCLUSIVE","evidence":{"error":type(e).__name__,"detail":str(e)[:230]}})
    print(json.dumps({"priority":"E1","experiments":rows},indent=2))
    return int(any(r["status"]=="INCONCLUSIVE" for r in rows))
if __name__=="__main__":raise SystemExit(main())
