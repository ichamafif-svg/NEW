"""P3 Campaign IV: boundary discrimination probes, NOT assertions of global guarantees.

Demonstrates K/T/U boundary through paired inputs at the actual legacy K
interfaces, plus positive permitted progress and local simulated provider call.
"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/"tests")]
from fixture import World,T0
from tcb.kernel import Refused

def witness(truth):
    w=World()
    grant,t=w.grant("agent",["effect:merge"],["repo:pr:*"],T0+1)
    reader,t=w.grant("readback",["evidence","observe","certify:real"],["repo:pr:*"],t)
    intent=w.add("intent","agent",t,under=grant,op="merge",args={"pr":"42","method":"squash"})
    g=w.guard(lambda *a:"ok");g.issue(intent,t+1);g.redeem(w.state["token_of"][intent],t+2)
    w.add("evidence","readback",w.state["last_at"]+1,
          under=reader,resource="repo:pr:42",subject=intent,level="real")
    return {"truth_outside_kernel":truth,"proof_obligation_open":"proof:"+intent in w.state["obligations"],
            "qualification":"ADMITTED","limit":"truth is deliberately absent from signed payload"}

def effect():
    w=World();grant,t=w.grant("agent",["effect:merge"],["repo:pr:*"],T0+1)
    intent=w.add("intent","agent",t,under=grant,op="merge",args={"pr":"42","method":"squash"})
    calls=[]
    def send(*a):calls.append(a[0]);return "unknown"
    g=w.guard(send);g.issue(intent,t+1);token=w.state["token_of"][intent]
    g.redeem(token,t+2)
    try:g.redeem(token,w.state["last_at"]+1);retry="ADMITTED"
    except Refused as e:retry=e.code
    return {"physical_calls_local":len(calls),"retry":retry,
            "reconcile_open":"reconcile:"+intent in w.state["obligations"],
            "limit":"local SQLite + fake EffectPort; unguarded provider credentials not present"}

def main():
    rows=[]
    for name,fn in (("P3-IV-P-true",lambda:witness(True)),
                    ("P3-IV-P-false",lambda:witness(False)),
                    ("P3-IV-E-unknown",effect)):
        try:rows.append({"id":name,"status":"OBSERVED","evidence":fn()})
        except Exception as e:rows.append({"id":name,"status":"INCONCLUSIVE",
             "evidence":{"error":type(e).__name__,"detail":str(e)[:240]}})
    print(json.dumps({"campaign":"IV","purpose":"boundary discrimination not formal proof",
                      "experiments":rows},indent=2))
    return int(any(x["status"]=="INCONCLUSIVE" for x in rows))
if __name__=="__main__":raise SystemExit(main())
