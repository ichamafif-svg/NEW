"""IV-B: discriminate K enforcement from T dependency with positive/negative controls.

All observations are local; a rejected call is not evidence of physical egress
exclusivity or independent human custody.
"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/"tests")]
from fixture import World,T0
from tcb.kernel import Refused
ARGS={"pr":"42","method":"squash"}

def boundary_effect():
    w=World()
    grant,t=w.grant("agent",["effect:merge"],["repo:pr:*"],T0+1)
    intent=w.add("intent","agent",t,under=grant,op="merge",args=ARGS)
    calls=[]
    g=w.guard(lambda *a:calls.append(a[0]) or "unknown")
    g.issue(intent,t+1)
    w.add("revoke","carol",t+2,grant=grant)
    try:
        g.redeem(w.state["token_of"][intent],t+3);result="ADMITTED"
    except Refused as e:result=e.code
    return {"kernel_guard_redeem":result,"physical_calls_via_guard":len(calls),
      "external_bypass_probe":"NOT_RUN: no alternate privileged credential",
      "safety_control":result!="ADMITTED" and len(calls)==0}

def unknown_retry():
    w=World();g_id,t=w.grant("agent",["effect:merge"],["repo:pr:*"],T0+1)
    iid=w.add("intent","agent",t,under=g_id,op="merge",args=ARGS)
    calls=[]
    guard=w.guard(lambda *a:calls.append(a[0]) or "unknown")
    guard.issue(iid,t+1)
    guard.redeem(w.state["token_of"][iid],t+2)
    try:
        w.add("intent","agent",w.state["last_at"]+1,under=g_id,op="merge",args=ARGS,retry_of=iid)
        outcome="ADMITTED"
    except Refused as e:outcome=e.code
    return {"retry":outcome,"port_calls":len(calls),
      "reconcile_debt":"reconcile:"+iid in w.state["obligations"],
      "physical_provider_truth":"UNOBSERVABLE","safety_control":outcome!="ADMITTED"}

def proof_contrast(wrong):
    w=World();gid,t=w.grant("agent",["effect:merge"],["repo:pr:*"],T0+1)
    rid,t=w.grant("readback",["evidence","observe","certify:real"],["repo:pr:*"],t)
    iid=w.add("intent","agent",t,under=gid,op="merge",args=ARGS)
    guard=w.guard(lambda *a:"ok");guard.issue(iid,t+1);guard.redeem(w.state["token_of"][iid],t+2)
    before="proof:"+iid in w.state["obligations"]
    try:
        w.add("evidence","readback",w.state["last_at"]+1,under=rid,
            resource="repo:pr:43" if wrong else "repo:pr:42",
            subject=iid,level="real")
        verdict="ADMITTED"
    except Refused as e:verdict=e.code
    return {"signed_claim_subject":"wrong" if wrong else "exact",
            "verdict":verdict,"proof_open_before":before,
            "proof_open_after":"proof:"+iid in w.state["obligations"],
            "external_measurement_truth":"UNOBSERVABLE",
            "control":verdict!="ADMITTED" if wrong else verdict=="ADMITTED"}

def main():
    funcs={"IVB-E-revoke":boundary_effect,"IVB-E-unknown":unknown_retry,
           "IVB-P-right":lambda:proof_contrast(False),"IVB-P-wrong":lambda:proof_contrast(True)}
    out=[]
    for name,fn in funcs.items():
        try:
            e=fn()
            status="OBSERVED" if (e.get("safety_control",e.get("control")) is True) else "VIOLATION_OBSERVED"
            out.append({"id":name,"status":status,"evidence":e})
        except Exception as ex:out.append({"id":name,"status":"INCONCLUSIVE",
                  "evidence":{"error":type(ex).__name__,"detail":str(ex)[:250]}})
    print(json.dumps({"campaign":"IV-B","experiments":out},indent=2))
    return int(any(c["status"]!="OBSERVED" for c in out))
if __name__=="__main__":raise SystemExit(main())
