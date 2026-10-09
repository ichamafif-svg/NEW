"""P3 observation-only long-horizon, reproducible autonomous-work sequences.

Exercises hundreds of signed requests and failed adversarial candidates on one
journal. Randomness is seeded and the result preserves the seed and event trace.
No new constitutional semantics, provider, or effect permission is created.
"""
from __future__ import annotations
import copy
import json
import random
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/"tests")]
from fixture import T0, World  # noqa: E402

SEEDS=(1,7,29,113,991)
EVENTS_PER_SEED=80


def scenario(seed):
    rng=random.Random(seed)
    w=World()
    gid,t=w.grant("agent",["effect:merge"],["repo:pr:*"],T0+1)
    events=[]
    accepted=refused=0
    distinct=set()
    for i in range(EVENTS_PER_SEED):
        # Advance by a small, deterministic, monotonically increasing increment.
        t+=1
        kind=rng.choice(("valid","invalid_authority","invalid_args","valid","valid","invalid_authority"))
        resource=str(1000+seed*100+i)
        args={"pr":resource,"method":"squash"}
        if kind=="valid":
            entry,ident=w.signed("intent","agent",t,under=gid,op="merge",args=args)
            should_admit=True
        elif kind=="invalid_authority":
            entry,ident=w.signed("intent","agent",t,under="not-a-grant",op="merge",args=args)
            should_admit=False
        else:
            entry,ident=w.signed("intent","agent",t,under=gid,op="merge",args={**args,"bypass":True})
            should_admit=False
        before=copy.deepcopy(w.state)
        allow,code,_=w.kernel.admit(w.state,entry)
        after=copy.deepcopy(w.state)
        assert before==after,"pure admission mutated state"
        assert allow==should_admit,("incorrect verdict",seed,i,kind,code)
        if allow:
            w.journal.append(entry)
            accepted+=1
            assert ident in w.state["intents"],"signed intent not materialized"
            assert w.state["intents"][ident]["resource"]=="repo:pr:"+resource
            distinct.add(resource)
        else:
            refused+=1
            assert w.state==w.journal.snapshot()
        events.append({"step":i,"variant":kind,"verdict":code,"size":w.state["size"]})
    assert len(distinct)==accepted
    assert accepted and refused
    assert w.state["size"]>=accepted
    return {"seed":seed,"attempts":len(events),"accepted":accepted,"refused":refused,
            "final_size":w.state["size"],"first":events[:3],"last":events[-3:],
            "limit":"independent resources, no dispatch; not proof of liveness"}


def main():
    rows=[]
    for seed in SEEDS:
        try:
            observation=scenario(seed)
            status="REFUTED_UNDER_ASSUMPTIONS"
        except Exception as e:
            observation={"exception":type(e).__name__,"detail":str(e)[:360]}
            status="INCONCLUSIVE"
        rows.append({"id":"P3-L"+str(seed),"status":status,"observation":observation})
    print(json.dumps({"baseline":"main@d6347dc","purpose":"long event horizons, no new abstraction",
                      "experiments":rows},indent=2))
    return int(any(x["status"]=="INCONCLUSIVE" for x in rows))


if __name__=="__main__":raise SystemExit(main())
