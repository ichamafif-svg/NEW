"""Phase 3 autonomy frontier: safety AND authorized progress.

An autonomous maintenance service is unacceptable both when untrusted agents
can gain authority and when no correctly authorized agent can make progress.
All probes use synthetic local fixtures and actual main admission / guard.
This suite is not a production liveness proof.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/"tests"))
from fixture import H,T0,World  # noqa: E402
from tcb.kernel import Refused  # noqa: E402

OPS={"pr":"42","method":"squash"}
results=[]


def case(ident,property_,fn):
    try:
        outcome=fn()
        status="REFUTED_UNDER_ASSUMPTIONS"
    except Exception as exc:
        status="INCONCLUSIVE"
        outcome={"error":type(exc).__name__,"detail":str(exc)[:300]}
    results.append({"id":ident,"property":property_,"status":status,"observation":outcome})


def refuse(w,kind,author,at,**kw):
    candidate,_=w.signed(kind,author,at,**kw)
    admitted,code,_=w.kernel.admit(w.state,candidate)
    assert not admitted,f"UNSAFE {kind} admission"
    return code


def autonomy_without_grant():
    w=World()
    code=refuse(w,"intent","agent",T0+1,under="unknown",op="merge",args=OPS)
    return {"unauthorized_intent":code}


def progress_under_valid_grant():
    w=World()
    gid,t=w.grant("agent",["effect:merge"],["repo:pr:*"],T0+1)
    iid=w.add("intent","agent",t,under=gid,op="merge",args=OPS)
    assert iid in w.state["intents"]
    return {"valid_intent":iid,"liveness":"one admitted intent"}


def wrong_resource_scope():
    w=World()
    gid,t=w.grant("agent",["effect:merge"],["repo:pr:41"],T0+1)
    code=refuse(w,"intent","agent",t,under=gid,op="merge",args=OPS)
    return {"scope_refusal":code}


def no_delegation_escalation():
    w=World()
    gid,t=w.grant("agent",["effect:merge"],["repo:pr:42"],T0+1)
    candidate,_=w.signed("delegate","agent",t,parent=gid,holder="ci",actions=["effect:merge"],
                          resources=["repo:*"],conditions=[],not_after=t+86_400_000)
    ok,code,_=w.kernel.admit(w.state,candidate)
    assert not ok,"delegation widened authority"
    return {"delegation_refusal":code}


def freeze_does_not_allow_intent():
    w=World()
    gid,t=w.grant("agent",["effect:merge"],["repo:pr:*"],T0+1)
    w.add("freeze","carol",t,scope="repo:pr:*")
    code=refuse(w,"intent","agent",t+1,under=gid,op="merge",args=OPS)
    return {"frozen_intent":code}


def revocation_does_not_allow_intent():
    w=World()
    gid,t=w.grant("agent",["effect:merge"],["repo:pr:*"],T0+1)
    w.add("revoke","carol",t,grant=gid)
    code=refuse(w,"intent","agent",t+1,under=gid,op="merge",args=OPS)
    return {"revoked_intent":code}


def valid_effect_does_not_discharge_own_proof():
    w=World()
    gid,t=w.grant("agent",["effect:merge"],["repo:pr:*"],T0+1)
    iid=w.add("intent","agent",t,under=gid,op="merge",args=OPS)
    guard=w.guard(lambda *args:"ok")
    guard.issue(iid,t+1)
    guard.redeem(w.state["token_of"][iid],t+2)
    assert f"proof:{iid}" in w.state["obligations"]
    return {"proof_due":True}


def reconciling_unknown_needs_independence():
    w=World()
    gid,t=w.grant("agent",["effect:merge"],["repo:pr:*"],T0+1)
    rid,t=w.grant("agent",["reconcile"],["repo:pr:*"],t)
    iid=w.add("intent","agent",t,under=gid,op="merge",args=OPS)
    guard=w.guard(lambda *args: (_ for _ in ()).throw(RuntimeError("lost ack")))
    guard.issue(iid,t+1)
    guard.redeem(w.state["token_of"][iid],t+2)
    code=refuse(w,"reconciliation","agent",w.state["last_at"]+1,
                under=rid,intent=iid,result="not_applied")
    return {"actor_self_reconciliation":code}


def budget_limits_autonomous_attempts():
    w=World()
    gid,t=w.grant("agent",["effect:merge"],["repo:pr:*"],T0+1,budget={"count":1,"window":86_400_000})
    a=w.add("intent","agent",t,under=gid,op="merge",args=OPS)
    b=w.add("intent","agent",t+1,under=gid,op="merge",args={"pr":"43","method":"squash"})
    guard=w.guard(lambda *args:"ok")
    guard.issue(a,t+2)
    try:
        guard.issue(b,t+3)
    except Refused as exc:
        return {"budget_refusal":exc.code}
    raise AssertionError("second token granted past budget")


def freeze_during_token_stage_blocks_dispatch():
    w=World()
    gid,t=w.grant("agent",["effect:merge"],["repo:pr:*"],T0+1)
    iid=w.add("intent","agent",t,under=gid,op="merge",args=OPS)
    calls=[]
    guard=w.guard(lambda *args:calls.append(args) or "ok")
    guard.issue(iid,t+1)
    w.add("freeze","sentinel",t+2,scope="repo:pr:*")
    try:
        guard.redeem(w.state["token_of"][iid],t+3)
    except Refused as exc:
        assert calls==[]
        return {"dispatch_blocked":exc.code,"calls":0}
    raise AssertionError("effect sent after freeze")


CASES=[
    ("P3-A01","no agent action without capability",autonomy_without_grant),
    ("P3-A02","authorized agent can still produce intent",progress_under_valid_grant),
    ("P3-A03","capability scoped to exact resource",wrong_resource_scope),
    ("P3-A04","delegation never widens",no_delegation_escalation),
    ("P3-A05","a freeze stops autonomous work",freeze_does_not_allow_intent),
    ("P3-A06","revoke stops autonomous work",revocation_does_not_allow_intent),
    ("P3-A07","effect result not equal independent proof",valid_effect_does_not_discharge_own_proof),
    ("P3-A08","agent cannot independently reconcile own intent",reconciling_unknown_needs_independence),
    ("P3-A09","bounded autonomous budget",budget_limits_autonomous_attempts),
    ("P3-A10","freeze between token and send",freeze_during_token_stage_blocks_dispatch),
]


def main():
    for ident,claim,fn in CASES:
        case(ident,claim,fn)
    print(json.dumps({"scope":"local main signed kernel + fake guard effects",
                      "attacks":results},indent=2))
    return int(any(x["status"]=="INCONCLUSIVE" for x in results))


if __name__=="__main__":
    raise SystemExit(main())
