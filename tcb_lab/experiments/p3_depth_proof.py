"""P3 campaign II: signed evidence truth contrasts; observation only."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/"tests")]
from fixture import World,T0
from tcb.kernel import Refused

def probe(variant,author="readback",resource="repo:pr:42",level="real",time_shift=1,truth=False):
    w=World()
    g,t=w.grant("agent",["effect:merge"],["repo:pr:*"],T0+1)
    read,t=w.grant("readback",["evidence","observe","certify:real"],["repo:pr:*"],t)
    subject=w.add("intent","agent",t,under=g,op="merge",args={"pr":"42","method":"squash"})
    guard=w.guard(lambda *args:"ok")
    guard.issue(subject,t+1);guard.redeem(w.state["token_of"][subject],t+2)
    before="proof:"+subject in w.state["obligations"]
    try:
        w.add("evidence",author,w.state["last_at"]+time_shift,under=read,
              resource=resource,subject=subject,level=level)
        verdict="ADMITTED"
    except Refused as exc:verdict=exc.code
    return {"variant":variant,"external_truth_label":truth,"author":author,
      "resource":resource,"level":level,"verdict":verdict,
      "proof_open_before":before,"proof_open_after":"proof:"+subject in w.state["obligations"],
      "scope":"truth label never entered signed evidence; adversary controls signed statement only"}

def main():
    cases=[
      ("true_exact",dict(truth=True)),
      ("false_exact",dict(truth=False)),
      ("wrong_subject",dict(resource="repo:pr:43",truth=True)),
      ("false_oracle_actor",dict(author="agent",truth=False)),
      ("claimed_lower_grade",dict(level="unknown",truth=False)),
      ("claimed_higher_grade",dict(level="real",truth=False)),
      ("future_timestamp",dict(time_shift=200000000,truth=False))]
    rows=[]
    for name,kw in cases:
        try:rows.append({"id":"P3-P2-"+name,"status":"OBSERVED","evidence":probe(name,**kw)})
        except Exception as exc:rows.append({"id":"P3-P2-"+name,"status":"INCONCLUSIVE","evidence":{"error":type(exc).__name__,"detail":str(exc)[:240]}})
    print(json.dumps({"priority":"P1","experiments":rows},indent=2))
    return int(any(x["status"]=="INCONCLUSIVE" for x in rows))
if __name__=="__main__":raise SystemExit(main())
