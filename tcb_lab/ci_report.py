"""Produce a sanitized Actions history and attack-result report in CI."""
import json
import os
from pathlib import Path
runs=json.loads(Path("ci-history.json").read_text()).get("workflow_runs",[])
root=Path("p3-artifacts")
names={
"g1-output.json":"G1 scope",
"p3-output.json":"P3 signed",
"p3-effects-output.json":"P3 effects",
"p3-mutation-output.json":"P3 mutations",
"p3-autonomy-output.json":"P3 autonomy",
"p3-compositions-output.json":"P3 compositions",
"p3-counter-output.json":"P3 counterexperiments",
"p3-long-horizon-output.json":"P3 long horizon",
"p3-priority-o1-output.json":"Priority O1 withdrawal",
"p3-priority-e1-output.json":"Priority E1 uncertain effect",
"p3-priority-p1-output.json":"Priority P1 signed false evidence",
"p3-depth-proof.json":"Depth P1 signed proof",
"p3-depth-effect.json":"Depth E1 effect retries",
"p3-depth-autonomy.json":"Depth O1 withdrawal replay",
"p3-iii-effect.json":"III E effect monotone retry",
"p3-iii-autonomy.json":"III O autonomy subjects",
"p3-iii-proof.json":"III P epistemic proof",
"p3-iv-boundary.json":"IV K/T/U boundary discriminators",
"p3-iv-matrix.json":"IV 16-guarantee matrix inventory",
"p3-ivb-pairs.json":"IV-B boundary paired contrasts",
"p3-ivc-scope.json":"IV-C conditional boundary scope audit",
"p3-ivc-target.json":"IV-C same target liveness",
}
rows=[]
for filename,desc in names.items():
    path=root/filename
    if not path.exists():
        rows.append((desc,"MISSING",0,0,"No artifact"))
        continue
    try:
        d=json.loads(path.read_text())
        cases=d.get("attacks",d.get("experiments",d.get("observations",d.get("cases",[]))))
        if not isinstance(cases,list) or not cases:
            raise ValueError("missing or empty experiment cases; an inventory audit must report at least one explicit observation")
        flagged=[]
        for x in cases:
            status=x.get("status",x.get("outcome"))
            evidence=x.get("evidence",x.get("observation",{}))
            broken=isinstance(evidence,dict) and (
                evidence.get("historic_assertions_hold") is False or
                (isinstance(evidence.get("historic_rule6_assertions"),dict) and
                 not all(evidence["historic_rule6_assertions"].values())))
            if status in {"INCONCLUSIVE","CONFIRMED","VIOLATION_OBSERVED","error"} or broken:
                flagged.append(str(x.get("id","?"))+(" (historical mismatch)" if broken else ""))
        rows.append((desc,"PARSED",len(cases),len(flagged),", ".join(flagged[:25]) or "none"))
    except Exception:
        rows.append((desc,"INVALID_JSON",0,0,"unreadable"))
def cell(v):
    return str(v if v is not None else "").replace("|","/").replace("\n"," ")[:110]
run=os.environ["REPORT_RUN_ID"]
repo=os.environ["GITHUB_REPOSITORY"]
lines=["# Standard TCB - automatic CI execution register","",
       "Generated after each laboratory CI run. A green workflow does not prove constitutional safety.","",
       "Latest tested run: https://github.com/"+repo+"/actions/runs/"+run,
       "Test job result: **"+os.environ["TEST_JOB_RESULT"]+"**","",
       "## Test verdicts per suite","",
       "| Suite | Artifact | Cases | Flagged | Flagged IDs |",
       "|---|---|---:|---:|---|"]
for row in rows:
    lines.append("| "+" | ".join(map(cell,row))+" |")
lines+=["","Flagged includes inconclusive, violation/error and OBSERVED scenarios diverging from a historical assertion. A green CI job can contain a scientific finding. No artifact does not mean PASS.","",
        "## Repository workflow history (last 100 runs)","",
        "| Workflow | Run | Branch | Conclusion | SHA |",
        "|---|---|---|---|---|"]
for item in runs[:100]:
    runlink="[#{0}]({1})".format(item.get("run_number","?"),item.get("html_url",""))
    lines.append("| "+" | ".join(map(cell,[item.get("name"),runlink,item.get("head_branch"),
                                            item.get("conclusion") or item.get("status"),
                                            (item.get("head_sha") or "")[:10]]))+" |")
lines+=["","## Boundaries outside current CI proof","",
        "Multi-host fencing, provider credential exclusivity, actual egress, quorum physical identity,",
        "false signed assertions, rollback of independent stores, and conditional liveness remain open.",""]
Path("ci-summary.md").write_text("\n".join(lines)+"\n")
print("history count:",len(runs),"suite results:",rows)
