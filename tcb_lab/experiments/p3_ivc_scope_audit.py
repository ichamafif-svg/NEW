"""IV-C research gate: audit guarantee allocation & explicit residual uncertainty.

A consistency instrument, not an empirical safety or liveness proof.
The document is the hypothesis under test, not the oracle.
"""
import json,re,sys
from pathlib import Path
base=Path(__file__).resolve().parents[1]
s=(base/"IVC_BOUNDARY_DECISIONS.md").read_text()
rows=[]
for ln in s.splitlines():
    parts=[x.strip() for x in ln.strip().strip("|").split("|")]
    if len(parts)==6 and re.fullmatch(r"G\d{2}",parts[0]):
        rows.append(parts)
ids=[x[0] for x in rows]
expected={f"G{i:02d}" for i in (2,5,7,8,9,10,11,12,13,14,15,16)}
duplicates=sorted({k for k in ids if ids.count(k)>1})
missing=sorted(expected-set(ids))
conditional=[r[0] for r in rows if r[4]=="CLOSED_CONDITIONAL"]
semantic=[r[0] for r in rows if r[4]=="OPEN_SEMANTIC"]
unverified=[r[0] for r in rows if r[5]!="BLOCKED_PHYSICAL" and r[5]!="OPEN_SEMANTIC"]
errors=[]
if missing or duplicates or len(rows)!=12:errors.append("incorrect_12_boundary_coverage")
if sorted(semantic)!=["G08","G16"]:errors.append("semantic_blockers_misaligned")
if len(conditional)!=10:errors.append("premature_or_missing_conditional_closure")
if unverified:errors.append("external_contract_marked_proven")
if any(not all(r[1:4]) for r in rows):errors.append("unspecified_K_T_or_falsifier")
print(json.dumps({"campaign":"IV-C","instrument":"scope-research-consistency",
"cases":[{"id":"IVC-coverage","status":"OBSERVED" if not errors else "INCONCLUSIVE",
"evidence":{"lines":len(rows),"missing":missing,"duplicates":duplicates,
"conditional_allocations":conditional,"semantic_open":semantic,
"premature_physical_claims":unverified,"errors":errors}}],
"limitation":"A document can be internally consistent and still false about real-world systems."},indent=2))
sys.exit(bool(errors))
