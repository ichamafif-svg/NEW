# F7: any craft failure (model off-scope answer, bad JSON, API outage) raises out of cmd_agent; in standard.yml
# `guard: needs: agent`, so no merge of any ready commit happens that run, and the same gap is retried first next run.
import sim as S
def craft(*a): raise ValueError("the repair of vulns leaves its write scope")
S.craft = craft
with S.Sim({"vulns": "found:1"}) as sim:
    for i in range(2):
        sim.clock.t += 400*60; sim.run("scan")
        try: sim.run("agent"); print("agent ok")
        except Exception as e: print("agent run", i, "CRASH:", e)
