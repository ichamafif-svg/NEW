"""Check current boundary-freeze documentation without rewriting historical IV-C counts."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
docs=["FUNCTIONAL_BOUNDARY_FREEZE_DECISION.md","SCOPE_FREEZE_REVIEW.md",
"TCB_BOUNDARY_MATRIX.md","GUARANTEE_MATRIX.md","ESTABLISHED_LIMITS.md",
"IVB_BOUNDARY_CLOSURE.md","IVC_BOUNDARY_DECISIONS.md",
"EXPERIMENT_TREE_DEPTH_COVERAGE.md","P3_EXIT_CRITERIA.md","README.md",
"findings/P3_LAB_STATUS.md","findings/P3_LAB_CHANGELOG.md","findings/README.md"]
decision=(ROOT/docs[0]).read_text()
ids=[f"G{i:02d}" for i in range(1,17)]
rows=[x for x in decision.splitlines() if x.startswith("| G") and x.count("|")>=5]
seen=[r.split("|")[1].strip() for r in rows]
missing=[d for d in docs if not (ROOT/d).exists() or
  ("FUNCTIONAL_BOUNDARY_FREEZE_DECISION.md" not in (ROOT/d).read_text() if d!=docs[0] else False)]
issues={"missing_or_unsynced":missing,"missing_ids":[i for i in ids if i not in seen],
"duplicates":sorted(set(i for i in seen if seen.count(i)>1)),
"decision_marker_missing":"16/16 CONDITIONAL_BOUNDARY_FROZEN" not in decision}
ok=not issues["missing_or_unsynced"] and not issues["missing_ids"] and not issues["duplicates"] and not issues["decision_marker_missing"]
print(json.dumps({"campaign":"BOUNDARY-FREEZE","experiments":[
 {"id":"BND-16-functional-allocations","status":"OBSERVED" if ok else "INCONCLUSIVE",
  "evidence":{"checked_documents":len(docs),"allocation_rows":len(rows),"issues":issues}}]},indent=2))
raise SystemExit(0 if ok else 1)
