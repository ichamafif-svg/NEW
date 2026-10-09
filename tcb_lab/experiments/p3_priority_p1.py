"""P3 P1: contrast cryptographically signed evidence and independently true evidence.

The trusted fixture can sign an intentionally false statement. This probes
kernel attribution, subject checking and obligation closure; it does not prove
real-world validity or claim that signing authentic data implies truth.
"""
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/"tests")]
from fixture import World,T0  # noqa
from tcb.kernel import Refused  # noqa
ARGS={"pr":"42","method":"squash"}

def case(name,resource,truth):
    w=World()
    grant,t=w.grant("agent",["effect:merge"],["repo:pr:*"],T0+1)
    reader,t=w.grant("readback",["evidence","observe","certify:real"],["repo:pr:*"],t)
    iid=w.add("intent","agent",t,under=grant,op="merge",args=ARGS)
    guard=w.guard(lambda *a:"ok")
    guard.issue(iid,t+1)
    guard.redeem(w.state["token_of"][iid],t+2)
    before="proof:"+iid in w.state["obligations"]
    try:
        w.add("evidence","readback",w.state["last_at"]+1,
              under=reader,resource=resource,subject=iid,level="real")
        admitted=True
        reason="ADMITTED"
    except Refused as exc:
        admitted=False
        reason=exc.code
    after="proof:"+iid in w.state["obligations"]
    return {"variant":name,"truth_known_to_synthetic_oracle":truth,
            "signed_readback_admitted":admitted,"verdict":reason,
            "proof_obligation_before":before,"proof_obligation_after":after,
            "signer":"readback","signer_truth_independent_of_signature":True}

def main():
    observations=[]
    for name,subject,truth in [("true_exact","repo:pr:42",True),
                               ("false_but_signed","repo:pr:42",False),
                               ("wrong_subject","repo:pr:43",True)]:
        try:
            observations.append({"id":"P3-P1-"+name,"status":"OBSERVED",
                                 "evidence":case(name,subject,truth)})
        except Exception as exc:
            observations.append({"id":"P3-P1-"+name,"status":"INCONCLUSIVE",
                                 "evidence":{"exception":type(exc).__name__,"detail":str(exc)[:280]}})
    print(json.dumps({"priority":"P1/O1","observations":observations,
                      "scope":"attestation contract local, fake physical truth flag"},indent=2))
    return int(any(x["status"]=="INCONCLUSIVE" for x in observations))

if __name__=="__main__":raise SystemExit(main())
