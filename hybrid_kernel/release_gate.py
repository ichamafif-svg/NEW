"""Release gate: inventory is not evidence; default must stay BLOCKED."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def report():
    data=json.loads((ROOT/"release_readiness.json").read_text())
    criteria=data["criteria"]
    ids=[x["id"] for x in criteria]
    if len(ids)!=len(set(ids)):
        raise ValueError("duplicate release criterion")
    required={"T"+f"{i:02}" for i in range(1,10)}
    if not required.issubset(ids):
        raise ValueError("missing Trusted External coverage")
    unverified=[{"id":x["id"],"status":x["status"]} for x in criteria
                if x.get("verified") is not True]
    return {"readiness":"BLOCKED" if unverified else "CANDIDATE_FOR_INDEPENDENT_REVIEW",
            "criteria":len(criteria),"unverified":unverified}
if __name__=="__main__":
    print(json.dumps(report(),indent=2))
    # Being BLOCKED is the expected result for this development branch.
