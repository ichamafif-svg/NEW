"""Campaign V baseline: corpus/document integrity, NOT an architecture implementation test."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
d=json.loads((root/"experiments/architecture_oracle_cases.json").read_text())
doc=(root/"ARCHITECTURE_CAMPAIGN_V.md").read_text()
cases=d["cases"]
ids=[c["id"] for c in cases]
guarantees={g for c in cases for g in c["guarantees"]}
missing=[f"G{i:02d}" for i in range(1,17) if f"G{i:02d}" not in guarantees]
valid={"ACCEPT","REJECT","PENDING_EXTERNAL","ESCALATION_DUE","UNRESOLVED"}
faults=[]
if missing:faults.append({"missing_guarantees":missing})
if len(ids)!=len(set(ids)):faults.append({"duplicate_case_ids":ids})
for c in cases:
    if c["expected"] not in valid or not c.get("scenario") or not c.get("invariant"):
        faults.append({"invalid_case":c.get("id")})
if any(x not in doc for x in ("A — moteur de transitions","B — moteur de contraintes","C — composition hybride","NO_CANDIDATE_SELECTED")):
    faults.append({"architecture_protocol":"incomplete"})
print(json.dumps({"campaign":"V-ARCH-BASELINE","experiments":[{
"id":"ARCH-V-corpus-integrity","status":"INCONCLUSIVE" if faults else "OBSERVED",
"evidence":{"cases":len(cases),"guarantees":len(guarantees),"faults":faults,
"limit":"Document corpus integrity only; no model implementation or security properties evaluated."}}]},indent=2))
raise SystemExit(bool(faults))
