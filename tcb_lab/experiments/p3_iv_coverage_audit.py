"""Campaign IV: fail-closed research coverage audit, not a constitutional proof.

Parse the boundary matrix and ensure all G01–G16 are explicitly classified,
their K/T/U cells are populated, and not confuse classification with evidence.
"""
import json,re,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
matrix=(root/"TCB_BOUNDARY_MATRIX.md").read_text()
limits=(root/"ESTABLISHED_LIMITS.md").read_text()
review=(root/"SCOPE_FREEZE_REVIEW.md").read_text()
rows={}
for line in matrix.splitlines():
    cols=[v.strip() for v in line.split("|")[1:-1]]
    if cols and re.fullmatch(r"G\d{2}",cols[0]):
        rows.setdefault(cols[0],[]).append(cols)
expected={f"G{i:02d}" for i in range(1,17)}
missing=sorted(expected-set(rows))
duplicate=sorted(i for i,r in rows.items() if len(r)!=1)
incomplete=sorted(i for i,items in rows.items()
                  if any(len(c)!=7 or any(not v.strip() for v in c[2:6]) for c in items))
limit_ids=sorted(set(re.findall(r"(?m)^## (L-\d{2})",limits)))
errors=[]
if missing:errors.append("unclassified_guarantees")
if duplicate:errors.append("duplicate_guarantees")
if incomplete:errors.append("incomplete_boundary_rows")
if not limit_ids:errors.append("no_declared_limits")
if "BOUNDARY VALIDATION INCOMPLETE" not in review:errors.append("premature_freeze_claim")
print(json.dumps({"campaign":"IV","kind":"research_instrument",
    "guarantees_expected":16,"guarantees_classified":len(rows),
    "missing":missing,"duplicates":duplicate,"incomplete":incomplete,
    "conditional_limits":limit_ids,"errors":errors,
    "status":"INCONCLUSIVE" if errors else "OBSERVED",
    "warning":"K/T/U inventory completeness is NOT empirical proof of physical safety"},
    indent=2))
sys.exit(bool(errors))
