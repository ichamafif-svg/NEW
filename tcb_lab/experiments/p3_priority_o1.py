"""Phase 3 O1: factual reproduction of the historical maintenance withdrawal red.

Do not assert the historic expected outcome as a new constitutional guarantee.
Record BOTH the expected test assertions and actual transitions. Comparison
across default_test variations separates runner behaviour from kernel verdict.
"""
import json
import io
from contextlib import redirect_stdout
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/"tests")]
from sim import Sim  # noqa
from ops import lifecycle  # noqa

def probe(label,verdict,cycles):
    with Sim({"vulns":"found:2"}) as sim:
        initial=sim.world.main_head()
        sim.default_test=verdict
        history=[]
        for n in range(cycles):
            with redirect_stdout(io.StringIO()):
                sim.cycle()
            phases=sim.subjects()
            node=sim.node()
            try: live=bool(lifecycle.live(node.state,node.now()))
            finally: node.close()
            history.append({"cycle":n+1,"head_unchanged":sim.world.main_head()==initial,
                            "phases":phases,"withdrawn_count":list(phases.values()).count("withdrawn"),
                            "live":live})
        last=history[-1]
        return {"variant":label,"test_result":verdict,"cycles":history,
                "historic_rule6_assertions":{"withdrawn_exactly_one":last["withdrawn_count"]==1,
                "base_head_intact":last["head_unchanged"],"no_live_subject":not last["live"]},
                "interpretation":"observed ops state; not a proof of TCB breach"}

def main():
    rows=[]
    for label,value,cycles in (("historic_red","found:1",2),("clean","none",2),
                                ("red_early","found:1",1),("red_longer","found:1",3)):
        try: rows.append({"id":"P3-O1-"+label,"status":"OBSERVED","evidence":probe(label,value,cycles)})
        except Exception as exc: rows.append({"id":"P3-O1-"+label,"status":"INCONCLUSIVE",
             "evidence":{"exception":type(exc).__name__,"detail":str(exc)[:220]}})
    print(json.dumps({"priority":"O1/R1","observations":rows},indent=2))
    return int(any(x["status"]=="INCONCLUSIVE" for x in rows))

if __name__=="__main__":raise SystemExit(main())
