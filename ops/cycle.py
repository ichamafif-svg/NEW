"""Standard maintenance cycle, one role per command. Each command runs with only that role's keys and tokens.

  init      humans: genesis (root + client law) and the grant proposals; witnesses: first checkpoint
  activate  humans: activate proposals whose witnessed delay has elapsed
  scan      scanner + witnesses: checkpoint, measure main, observe agent pull requests, read back merges
  ask       agent: ask the law to merge commits the scanner observed ready (fast, inside the witnessed window)
  repair    agent: prepare at most one new repair pull request with Claude (slow, writes no journal entry)
  guard     guard: token, durable reservation, rejudgment, merge through the GitHub adapter
  attest    compliance officer: attest an organisational measure
  report    anyone: health, work plan, compliance dossier (JSON + HTML), status for the dashboard

State lives in a directory (journal/ and pins/ are independent restore domains; genesis.json holds the pin)."""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tcb.floors import FLOORS, floors_digest  # noqa: E402
from tcb import EffectPort, Guard, Refused  # noqa: E402

from ops import scan  # noqa: E402
from ops.node import HUMANS, Node, load_keys, root_of  # noqa: E402

DAY = 86_400_000
TECH = {t["id"]: t for t in FLOORS["targets"] if t.get("repair") == "remediate" or t["id"] in ("branch", "inventory")}
REMEDIATE = ["repo:deps:*", "repo:code:*", "repo:ci:*", "repo:supply:*"]


def law() -> dict:
    return {"format": "standard-client/1", "floors": floors_digest(),
            "bindings": {"owner": "icham", "inventory_source": "scanner", "scanner": "scanner",
                         "compliance_officer": "second"}, "targets": []}


GRANTS = [
    {"holder": "agent", "actions": ["effect:remediate"], "resources": REMEDIATE, "conditions": ["remediate-autonomous"]},
    {"holder": "agent", "actions": ["effect:remediate"], "resources": REMEDIATE, "conditions": ["remediate-reviewed"]},
    {"holder": "scanner", "actions": ["observe", "certify:real", "evidence", "reconcile"], "resources": ["repo:*"],
     "conditions": []},
    {"holder": "second", "actions": ["observe", "certify:real"], "resources": ["org:*"], "conditions": []},
]


def grant_of(s, holder, condition=None, action=None):
    now = s["last_at"]
    for g in s["grants"].values():
        if (g["holder"] == holder and g["id"] not in s["revoked"] and g["not_after"] > now
                and (condition is None or list(g["conditions"]) == [condition])
                and (action is None or action in g["actions"])):
            return g["id"]
    return None


def cmd_init(node: Node, a):
    if node.genesis:
        raise SystemExit("this state directory already has a genesis")
    publics = json.loads(Path(a.publics).read_text())
    node.add("genesis", "icham", HUMANS, root=root_of(publics), law=law(), code=node.kernel.code_pin,
             at=int(time.time() * 1000))
    pin = node.state["domain"]
    (node.dir / "genesis.json").write_text(json.dumps({"pin": pin}))
    node.genesis = node.journal.genesis_pin = pin
    node.pins.bind(pin)
    node.retain()
    node.checkpoint()
    until = int(time.time() * 1000) + a.days * DAY
    for g in GRANTS:
        node.add("grant", "icham", HUMANS, **g, not_after=until)
    print(json.dumps({"genesis": pin, "proposals": len(GRANTS)}))


def cmd_activate(node: Node, a):
    node.checkpoint()
    done = []
    for pid in list(node.state["proposals"]):
        try:
            node.add("activate", "icham", HUMANS, proposal=pid)
            done.append(pid)
        except Refused as r:
            print(f"{pid}: {r.code} {r.detail}")
    print(json.dumps({"activated": done}))


def observe(node: Node, under, resource, prop, status, refresh_ms=6 * 3_600_000):
    """Sign only what changed, or what is about to go stale: facts are evidence, not a heartbeat."""
    s = node.state
    last = s["observations"].get(f"{resource}|{prop}|scanner")
    if last and last["status"] == status and node.now() - last["at"] < refresh_ms:
        return False
    node.add("observation", "scanner", under=under, resource=resource, property=prop, status=status, level="real")
    return True


def cmd_scan(node: Node, a):
    from ops.gh import Client
    gh = Client(a.repo, os.environ["GITHUB_TOKEN"])
    node.checkpoint()
    under = grant_of(node.state, "scanner", action="observe")
    if under is None:
        raise SystemExit("the scanner has no active grant yet")
    measured = scan.measure(Path(a.checkout), gh)
    targets = {t["id"]: t for t in FLOORS["targets"]}
    written = 0
    for tid, status in measured.items():
        t = targets[tid]
        written += observe(node, under, t["resource"], t["property"], status)
    complete = not any(str(v).startswith("error:") for v in measured.values())
    written += observe(node, under, "repo:inventory:all", "coverage", "complete" if complete else "partial")
    for resource, prop, status in scan.pull_facts(gh, a.agent_login):
        written += observe(node, under, resource, prop, status)
    s = node.state
    for iid, it in s["intents"].items():                     # read back: did GitHub merge exactly this commit?
        if it["op"] != "remediate":
            continue
        line = s["line"].get(iid, {}).get("state")
        if f"proof:{iid}" not in s["obligations"] and line not in ("uncertain", "expired"):
            continue
        pull = gh.pull(it["args"]["pr"])
        landed = bool(pull.get("merged")) and pull["head"]["sha"] == it["args"]["head"]
        if line in ("uncertain", "expired"):                 # an outcome nobody knows is settled by reading back
            node.add("reconciliation", "scanner", under=under, intent=iid,
                     result="applied" if landed else "not_applied")
            written += 1
            s = node.state
        if landed and f"proof:{iid}" in s["obligations"]:
            node.add("evidence", "scanner", under=under, resource=it["resource"], subject=iid, level="real")
            written += 1
    node.retain()
    print(json.dumps({"measured": measured, "written": written}))


def cmd_ask(node: Node, a):
    """Ask the law to merge every commit the scanner observed ready. Fast: it runs inside the witnessed window."""
    s = node.state
    latest = {}                                                # (pr, head) -> its most recent intent
    for iid, it in s["intents"].items():
        if it["op"] == "remediate":
            key = (it["args"]["pr"], it["args"]["head"])
            if key not in latest or it["stmt"]["at"] >= latest[key]["stmt"]["at"]:
                latest[key] = it
    facts, seen_at = {}, {}
    for o in s["observations"].values():
        if "/pr/" in o["resource"] and o["author"] == "scanner":
            facts.setdefault(o["resource"], {})[o["property"]] = o["status"]
            seen_at[o["resource"]] = max(seen_at.get(o["resource"], 0), o["at"])
    intents = []
    for resource, f in sorted(facts.items()):
        base, _, rest = resource.partition("/pr/")
        pr, head = rest.split("/")
        _, area, item = base.split(":")
        prior = latest.get((pr, head))
        retry = None
        if prior is not None:
            # Ask again only after a definite failure (GitHub merged nothing) and a newer observation of the commit.
            if s["line"].get(prior["id"], {}).get("state") != "failed" or seen_at[resource] <= prior["stmt"]["at"]:
                continue
            retry = prior["id"]
        if f.get("ci") != "green":
            continue
        cond = "remediate-autonomous" if f.get("scope") == "dependencies" else (
            "remediate-reviewed" if f.get("review") == "approved" else None)
        under = cond and grant_of(s, "agent", condition=cond)
        if not under:
            continue
        try:
            fields = {"retry_of": retry} if retry else {}
            node.add("intent", "agent", under=under, op="remediate",
                     args={"area": area, "item": item, "pr": pr, "head": head, "method": "squash"}, **fields)
            intents.append(pr)
        except Refused as r:
            print(f"intent for #{pr} refused: {r.code} {r.detail}")
    node.retain()
    print(json.dumps({"intents": intents}))


def cmd_repair(node: Node, a):
    """Prepare at most one new repair pull request. Slow (Claude); it writes nothing to the journal."""
    from ops.gh import Client
    from ops import agent
    gh = Client(a.repo, os.environ["AGENT_GITHUB_TOKEN"])
    s = node.state
    opened = []
    open_targets = {p["head"]["ref"].split("/")[2] for p in gh.pulls() if p["head"]["ref"].startswith("standard/")}
    health = json.loads(Path(a.health).read_text()) if a.health else None
    gaps = [o for o in (health or {}).get("open", []) + (health or {}).get("escalated", [])
            if o.get("type") == "target" and TECH.get(o.get("target"), {}).get("repair") == "remediate"]
    for gap in sorted(gaps, key=lambda o: o["due"]):
        t = TECH[gap["target"]]
        _, area, item = t["resource"].split(":")
        seen = s["observations"].get(f"{t['resource']}|{t['property']}|scanner")
        status = seen["status"] if seen else None
        if item in open_targets or status in (None, t["expect"]) or status.startswith("error:"):
            continue                                          # already in review, unmeasured, or only stale
        pull = agent.open_repair(Path(a.checkout), gh, t["id"], area, item, status, os.environ.get("ANTHROPIC_API_KEY", ""))
        if pull:
            opened.append(pull.get("number"))
            break                                             # one new repair per cycle keeps review possible
    print(json.dumps({"opened": opened}))


def cmd_guard(node: Node, a):
    from adapters.github import GitHub
    port = EffectPort(GitHub(a.repo, os.environ["MERGE_TOKEN"]).ports())
    guard = Guard(node.journal, "guard", node.signer("guard"), port)
    s, results = node.state, {}
    for iid, it in s["intents"].items():
        if it["op"] != "remediate" or s["line"].get(iid, {}).get("state") != "intended":
            continue
        try:
            guard.issue(iid, node.now())
            tid = node.state["token_of"][iid]
            guard.redeem(tid, node.now())
            results[iid] = node.state["executed"].get(tid)
        except Refused as r:
            results[iid] = f"refused {r.code}"
    node.retain()
    print(json.dumps(results))


def cmd_attest(node: Node, a):
    node.checkpoint()
    under = grant_of(node.state, "second", action="observe")
    resource, prop, status = (("org:controls:soa", "coverage", "complete") if a.resource == "org:controls:soa"
                              else (a.resource, "attested", "current"))
    node.add("observation", "second", under=under, resource=resource, property=prop, status=status, level="real")
    node.retain()


def cmd_report(node: Node, a):
    from compliance.dossier import build, render, rows_of
    from maintenance.planner import plan
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    node.retain()
    health = node.journal.health(required_at=int(time.time() * 1000))
    (out / "health.json").write_text(json.dumps(health, indent=1))
    (out / "plan.json").write_text(json.dumps(plan(health), indent=1))
    s = node.state
    dossier = build(rows_of(node.journal.path), genesis_pin=node.genesis, checkpoints=node.pins.load(),
                    required_at=health["evaluated_at"])
    (out / "dossier.json").write_text(json.dumps(dossier, ensure_ascii=False, indent=1))
    (out / "dossier.html").write_text(render(dossier))
    lines = list(s["line"].values())
    status = {"at": health["evaluated_at"], "state": health["state"], "size": s["size"], "head": s["head"],
              "merged": sum(1 for v in s["executed"].values() if v == "ok"),
              "refused_or_failed": sum(1 for v in s["executed"].values() if v != "ok"),
              "intents": len(s["intents"]), "proven": len(health["proven"]),
              "open": len(health["open"]), "escalated": len(health["escalated"]),
              "lines": {k: sum(1 for x in lines if x["state"] == k) for k in {x["state"] for x in lines}},
              "frameworks": {f["id"]: f["counts"] for f in dossier["frameworks"]}}
    (out / "status.json").write_text(json.dumps(status, ensure_ascii=False, indent=1))
    print(json.dumps(status, ensure_ascii=False))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m ops")
    ap.add_argument("command", choices=["init", "activate", "scan", "ask", "guard", "repair", "attest", "report"])
    ap.add_argument("--state", required=True)
    ap.add_argument("--keys", help="JSON key file; default: STANDARD_KEYS")
    ap.add_argument("--publics")
    ap.add_argument("--days", type=int, default=90)
    ap.add_argument("--repo")
    ap.add_argument("--checkout", default=".")
    ap.add_argument("--agent-login", default="standard-agent")
    ap.add_argument("--health")
    ap.add_argument("--resource")
    ap.add_argument("--out", default="report")
    ap.add_argument("--genesis", help="externally kept genesis pin (default: STANDARD_GENESIS)")
    a = ap.parse_args(argv)
    expected = a.genesis or os.environ.get("STANDARD_GENESIS")
    if a.command != "init" and not expected:
        raise SystemExit("the genesis pin must come from outside the state: --genesis or STANDARD_GENESIS")
    node = Node(a.state, load_keys(a.keys), create=a.command == "init", expected_genesis=expected)
    try:
        globals()["cmd_" + a.command](node, a)
    finally:
        node.close()


if __name__ == "__main__":
    main()
