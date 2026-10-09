"""P3 E1: uncertain effect permutations with separate real signed journals.

Synthetic port only. Explore sent+lost ACK, explicit unknown, failed/no-send,
positive success. An actual provider may violate the synthetic port semantics.
"""
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/"tests")]
from fixture import World,T0  # noqa
from tcb.kernel import Refused  # noqa

ARGS={"pr":"42","method":"squash"}
def probe(label,response):
    w=World()
    grant,t=w.grant("agent",["effect:merge"],["repo:pr:*"],T0+1)
    iid=w.add("intent","agent",t,under=grant,op="merge",args=ARGS)
    sends=[]
    def callback(*args):
        sends.append({"resource":args[1],"args":args[2]})
        if response=="raise":raise RuntimeError("ack lost after provider possibly applied")
        return response
    guard=w.guard(callback)
    guard.issue(iid,t+1)
    guard.redeem(w.state["token_of"][iid],t+2)
    state=w.state
    obligations=sorted(k for k in state["obligations"] if iid in k)
    try:
        w.add("intent","agent",state["last_at"]+1,under=grant,op="merge",args=ARGS,retry_of=iid)
        retry="admitted"
    except Refused as exc:retry=exc.code
    return {"variant":label,"simulated_response":response,"send_count":len(sends),
            "executed":state["executed"][state["token_of"][iid]],"obligations":obligations,
            "retry_verdict":retry,"limit":"local simulated provider: no physical egress or delayed ACK"}
def main():
    cases=[]
    for name,r in [("ack_lost","raise"),("explicit_unknown","unknown"),
                   ("success","ok"),("failed_report","failed")]:
        try: cases.append({"id":"P3-E1-"+name,"status":"OBSERVED","evidence":probe(name,r)})
        except Exception as exc: cases.append({"id":"P3-E1-"+name,"status":"INCONCLUSIVE",
                  "evidence":{"exception":type(exc).__name__,"detail":str(exc)[:300]}})
    print(json.dumps({"priority":"E1","observations":cases},indent=2))
    return int(any(c["status"]=="INCONCLUSIVE" for c in cases))
if __name__=="__main__":raise SystemExit(main())
