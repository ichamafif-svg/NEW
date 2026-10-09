"""Phase 3 campaign III — isolate retry refusal from historical clock rejection.

Observed-only: synthetic effect port and shared local SQLite. A repeated token
is attempted at strictly later time than the last committed journal event.
"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/"tests")]
from fixture import World,T0
from tcb.kernel import Refused

def experiment(response,another):
    w=World()
    grant,t=w.grant("agent",["effect:merge"],["repo:pr:*"],T0+1)
    iid=w.add("intent","agent",t,under=grant,op="merge",args={"pr":"42","method":"squash"})
    calls=[]
    def execute(*args):
        calls.append(args[0])
        if response=="ack_lost":raise OSError("simulated lost ACK")
        return response
    guard=w.guard(execute)
    guard.issue(iid,t+1)
    token=w.state["token_of"][iid]
    guard.redeem(token,t+2)
    last=w.state["last_at"]
    candidate=w.guard(execute,journal=w.other_journal()) if another else guard
    try:
        candidate.redeem(token,last+1)
        verdict="ADMITTED"
    except Refused as e:verdict=e.code
    return {"variant":response,"independent_journal_handle":another,"first_state":w.state["executed"][token],
        "last_committed_time":last,"second_attempt_time":last+1,
        "second_attempt_verdict":verdict,"synthetic_calls":len(calls),
        "open_obligations":sorted(x for x in w.state["obligations"] if iid in x),
        "limitations":"one local SQLite database and fake provider; no process/host isolation"}

def main():
    rows=[]
    for response in ("ack_lost","unknown","ok","failed"):
        for another in (False,True):
            id="P3-III-E-"+response+("-other" if another else "-same")
            try:rows.append({"id":id,"status":"OBSERVED","evidence":experiment(response,another)})
            except Exception as e:rows.append({"id":id,"status":"INCONCLUSIVE","evidence":{"error":type(e).__name__,"detail":str(e)[:300]}})
    print(json.dumps({"campaign":"III","branch":"E","experiments":rows},indent=2))
    return int(any(r["status"]=="INCONCLUSIVE" for r in rows))
if __name__=="__main__":raise SystemExit(main())
