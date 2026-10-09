"""P3 exploration: paired safety/progress probes after an adversarial disturbance.

This is not a candidate architecture. Each experiment has a positive control
and a negative adversarial case, testing whether refusal contaminates a later
legitimate opportunity. Real signed Journal, local fake EffectPort.
"""
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/"tests")]
from fixture import World,T0  # noqa: E402
from tcb.kernel import Refused  # noqa: E402

CASES=[]


def run_case(name,fn):
    try:
        data=fn()
        status="REFUTED_UNDER_ASSUMPTIONS"
    except Exception as e:
        data={"error":type(e).__name__,"detail":str(e)[:280]}
        status="INCONCLUSIVE"
    CASES.append({"id":name,"status":status,"observation":data})


def expect_refusal(fn):
    try: fn()
    except Refused as e: return e.code
    raise AssertionError("unexpected admission")


def base():
    w=World()
    gid,t=w.grant("agent",["effect:merge"],["repo:pr:*"],T0+1)
    return w,gid,t


def forged_attempt_then_valid_intent():
    w,g,t=base()
    bad=expect_refusal(lambda:w.add("intent","agent",t,under="nonexistent",op="merge",args={"pr":"42","method":"squash"}))
    legit=w.add("intent","agent",t+1,under=g,op="merge",args={"pr":"42","method":"squash"})
    assert legit in w.state["intents"]
    return {"rejected":bad,"valid_progress":True}


def wrong_scope_then_valid_scope():
    w,g,t=base()
    bad=expect_refusal(lambda:w.add("intent","agent",t,under=g,op="merge",args={"pr":"42","method":"squash","admin":True}))
    legit=w.add("intent","agent",t+1,under=g,op="merge",args={"pr":"43","method":"squash"})
    assert w.state["intents"][legit]["resource"]=="repo:pr:43"
    return {"rejected":bad,"valid_progress":True}


def duplicate_token_then_new_independent_intent():
    w,g,t=base()
    a=w.add("intent","agent",t,under=g,op="merge",args={"pr":"42","method":"squash"})
    guard=w.guard(lambda *args:"ok")
    guard.issue(a,t+1)
    first_token=w.state["token_of"][a]
    bad=expect_refusal(lambda:guard.issue(a,t+2))
    b=w.add("intent","agent",t+3,under=g,op="merge",args={"pr":"43","method":"squash"})
    guard.issue(b,t+4)
    assert w.state["token_of"][b]!=first_token
    return {"rejected":bad,"other_resource_progress":True}


def wrong_proof_then_valid_independent_proof():
    w,g,t=base()
    observer,t=w.grant("readback",["evidence","observe","certify:real"],
                       ["repo:pr:*"],t)
    intent=w.add("intent","agent",t,under=g,op="merge",args={"pr":"42","method":"squash"})
    guard=w.guard(lambda *args:"ok")
    guard.issue(intent,t+1)
    guard.redeem(w.state["token_of"][intent],t+2)
    at=w.state["last_at"]+1
    bad=expect_refusal(lambda:w.add("evidence","readback",at,under=observer,
                                    resource="repo:pr:43",subject=intent,level="real"))
    w.add("evidence","readback",at+1,under=observer,
          resource="repo:pr:42",subject=intent,level="real")
    assert "proof:"+intent not in w.state["obligations"]
    return {"wrong_subject_refused":bad,"correct_proof_closed":True}


def unknown_result_does_not_close_proof():
    w,g,t=base()
    a=w.add("intent","agent",t,under=g,op="merge",args={"pr":"42","method":"squash"})
    guard=w.guard(lambda *args:"unknown")
    guard.issue(a,t+1)
    guard.redeem(w.state["token_of"][a],t+2)
    assert "reconcile:"+a in w.state["obligations"]
    assert "proof:"+a not in w.state["obligations"]
    return {"reconcile_open":True,"proof_not_assumed":True}


PROGRAM={
"P3-D01":forged_attempt_then_valid_intent,
"P3-D02":wrong_scope_then_valid_scope,
"P3-D03":duplicate_token_then_new_independent_intent,
"P3-D04":wrong_proof_then_valid_independent_proof,
"P3-D05":unknown_result_does_not_close_proof,
}


def main():
    for name,fn in PROGRAM.items():run_case(name,fn)
    print(json.dumps({"scope":"phase-3 observation-only, local journal and effect stub",
                      "experiments":CASES},indent=2))
    return int(any(c["status"]!="REFUTED_UNDER_ASSUMPTIONS" for c in CASES))


if __name__=="__main__":raise SystemExit(main())
