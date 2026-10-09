"""P3 campaign III — epistemic equivalence and actual payload contrasts.

External truth is intentionally not present in signed payload. Repeat same
claim with different truth labels to distinguish cryptographic qualification
from unobservable physical truth. No inference of external oracle independence.
"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/"tests")]
from p3_depth_proof import probe

def main():
    cases=[]
    variants=[("claimed_real_true",dict(level="real",truth=True)),
              ("claimed_real_false",dict(level="real",truth=False)),
              ("claimed_unknown_false",dict(level="unknown",truth=False)),
              ("wrong_subject_false",dict(resource="repo:pr:43",truth=False)),
              ("unauthorized_false",dict(author="agent",truth=False)),
              ("ahead_false",dict(time_shift=200000000,truth=False))]
    for name,kw in variants:
        try:cases.append({"id":"P3-III-P-"+name,"status":"OBSERVED","evidence":probe(name,**kw)})
        except Exception as exc:cases.append({"id":"P3-III-P-"+name,"status":"INCONCLUSIVE",
            "evidence":{"error":type(exc).__name__,"detail":str(exc)[:240]}})
    facts={v["id"].split("P3-III-P-")[-1]:v.get("evidence",{}) for v in cases}
    if all(v["status"]=="OBSERVED" for v in cases):
        facts["epistemic_check"]={"same_verdict_when_only_external_truth_changes":
            facts["claimed_real_true"]["verdict"]==facts["claimed_real_false"]["verdict"],
            "same_proof_closure_when_only_external_truth_changes":
            facts["claimed_real_true"]["proof_open_after"]==facts["claimed_real_false"]["proof_open_after"],
            "interpretation":"unobservable truth label: not a constitutional safety violation"}
    print(json.dumps({"campaign":"III","branch":"P","experiments":cases,
                      "cross_case_observation":facts.get("epistemic_check",{})},indent=2))
    return int(any(x["status"]=="INCONCLUSIVE" for x in cases))
if __name__=="__main__":raise SystemExit(main())
