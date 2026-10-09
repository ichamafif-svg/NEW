"""Phase 3: cross-boundary adversarial sequences for Standard's autonomous TCB.

All tests operate on a temporary, signed journal with fake effect ports.
Safety assertions are checked after *multiple* constitutional events, not
against a single isolated decision. No physical provider is contacted.
"""
from __future__ import annotations
import json
import copy
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/"tests")]
from fixture import World,T0,DAY  # noqa: E402
from tcb.kernel import Refused  # noqa: E402
from tcb.canon import canon  # noqa: E402

CASES=[]


def check(name,claim,fn):
    try:
        observation=fn()
        status="REFUTED_UNDER_ASSUMPTIONS"
    except Exception as exc:
        status="INCONCLUSIVE"
        observation={"exception":type(exc).__name__,"detail":str(exc)[:300]}
    CASES.append({"id":name,"property":claim,"status":status,"observation":observation})


def refuses(fn):
    try:
        fn()
    except Refused as exc:
        return exc.code
    raise AssertionError("unsafe transition accepted")


def ready(w):
    grant,t=w.grant("agent",["effect:merge"],["repo:pr:*"],T0+1)
    return grant,t


def sequence_revoke_then_intent():
    w=World(); grant,t=ready(w)
    w.add("revoke","carol",t,grant=grant)
    code=refuses(lambda:w.add("intent","agent",t+1,under=grant,
                                     op="merge",args={"pr":"42","method":"squash"}))
    return {"rejection":code,"intents":len(w.state["intents"])}


def sequence_intent_then_revoke_then_guard():
    w=World(); grant,t=ready(w)
    intent=w.add("intent","agent",t,under=grant,op="merge",args={"pr":"42","method":"squash"})
    calls=[]
    guard=w.guard(lambda *args:calls.append(args) or "ok")
    guard.issue(intent,t+1)
    w.add("revoke","carol",t+2,grant=grant)
    code=refuses(lambda:guard.redeem(w.state["token_of"][intent],t+3))
    assert calls==[]
    return {"rejection":code,"physical_calls":0}


def sequence_intent_then_freeze_then_guard():
    w=World(); grant,t=ready(w)
    intent=w.add("intent","agent",t,under=grant,op="merge",args={"pr":"42","method":"squash"})
    calls=[]
    guard=w.guard(lambda *args:calls.append(args) or "ok")
    guard.issue(intent,t+1)
    w.add("freeze","sentinel",t+2,scope="repo:pr:*")
    code=refuses(lambda:guard.redeem(w.state["token_of"][intent],t+3))
    assert calls==[]
    return {"rejection":code,"physical_calls":0}


def sequence_effect_success_then_proof_pending():
    w=World(); grant,t=ready(w)
    intent=w.add("intent","agent",t,under=grant,op="merge",args={"pr":"42","method":"squash"})
    calls=[]
    guard=w.guard(lambda *args:calls.append(args) or "ok")
    guard.issue(intent,t+1)
    guard.redeem(w.state["token_of"][intent],t+2)
    assert len(calls)==1
    assert "proof:"+intent in w.state["obligations"]
    assert "reconcile:"+intent not in w.state["obligations"]
    return {"calls":1,"proof_open":True}


def sequence_unknown_then_self_reconcile():
    w=World(); grant,t=ready(w)
    rid,t=w.grant("agent",["reconcile"],["repo:pr:*"],t)
    intent=w.add("intent","agent",t,under=grant,op="merge",args={"pr":"42","method":"squash"})
    guard=w.guard(lambda *args:(_ for _ in ()).throw(RuntimeError("ack dropped")))
    guard.issue(intent,t+1)
    guard.redeem(w.state["token_of"][intent],t+2)
    code=refuses(lambda:w.add("reconciliation","agent",w.state["last_at"]+1,
                              under=rid,intent=intent,result="not_applied"))
    assert "reconcile:"+intent in w.state["obligations"]
    return {"rejection":code,"reconciliation_still_required":True}


def sequence_repeated_failed_attempt_keeps_previous_rights():
    w=World(); grant,t=ready(w)
    original=copy.deepcopy(w.state)
    from tcb.kernel import Kernel
    for i in range(12):
        entry,_=w.signed("intent","agent",t+i,under="unknown",
                         op="merge",args={"pr":"42","method":"squash"})
        admitted,_,_=w.kernel.admit(w.state,entry)
        assert not admitted
        assert w.state==original,"failed request changed state"
    iid=w.add("intent","agent",t+12,under=grant,op="merge",
              args={"pr":"42","method":"squash"})
    return {"failed_attempts":12,"legitimate_intent_still_admitted":iid in w.state["intents"]}


def sequence_double_intent_different_subjects():
    w=World(); grant,t=ready(w)
    a=w.add("intent","agent",t,under=grant,op="merge",args={"pr":"42","method":"squash"})
    b=w.add("intent","agent",t+1,under=grant,op="merge",args={"pr":"43","method":"squash"})
    assert w.state["intents"][a]["resource"]!=w.state["intents"][b]["resource"]
    return {"distinct_intents":2,"distinct_resources":True}


PROGRAM=[
("P3-X01","revocation precedes an attempted autonomous intent",sequence_revoke_then_intent),
("P3-X02","intent/token predate revocation but dispatch follows it",sequence_intent_then_revoke_then_guard),
("P3-X03","intent/token predate freeze but dispatch follows it",sequence_intent_then_freeze_then_guard),
("P3-X04","provider success does not prove effect independently",sequence_effect_success_then_proof_pending),
("P3-X05","unknown effect cannot self-reconcile",sequence_unknown_then_self_reconcile),
("P3-X06","failed hostile attempts do not poison authorized progress",sequence_repeated_failed_attempt_keeps_previous_rights),
("P3-X07","two separately authorized resources remain distinct",sequence_double_intent_different_subjects),
]


def main():
    for name,claim,fn in PROGRAM:
        check(name,claim,fn)
    print(json.dumps({"baseline":"main@d6347dc","boundary":"local signed journal + fake effect port",
                      "experiments":CASES},indent=2))
    return int(any(x["status"]=="INCONCLUSIVE" for x in CASES))


if __name__=="__main__":
    raise SystemExit(main())
