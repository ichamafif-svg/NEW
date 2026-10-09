"""Standard maintenance, one role per command. A role holds only its own keys and tokens and acts only on what the
journal names.

  init      humans: genesis (root + client law) and the grant proposals; witnesses: first checkpoint
  activate  humans: activate proposals whose witnessed delay has elapsed
  scan      scanner + witnesses: checkpoint, measure main, observe declared commits, reconcile and prove effects
  agent     agent: ask the law for ready commits, then craft and declare at most one new repair
  guard     guard: token, durable reservation, rejudgment, merge through the trusted GitHub adapter
  review    a human: approve one declared commit
  attest    the compliance officer: attest an organisational measure
  report    anyone: health, work plan, compliance dossier (JSON + HTML), status

What a role does next comes from ops.lifecycle (the kernel's effect automaton); what the world is asked comes from
ops.world (questions about named subjects only); what a probe concludes comes from ops.probes.verdict."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tcb import EffectPort, Guard, Refused  # noqa: E402
from tcb.floors import FLOORS, floors_digest  # noqa: E402

from ops import agent, lifecycle, probes  # noqa: E402
from ops.node import HUMANS, Node, load_keys, root_of  # noqa: E402

DAY = 86_400_000
TARGETS = {t["id"]: t for t in FLOORS["targets"]}
REMEDIATE = ["repo:deps:*", "repo:code:*", "repo:ci:*", "repo:supply:*"]
DEPENDENCY_FILES = r"(requirements[A-Za-z0-9_.-]*\.txt|pyproject\.toml|poetry\.lock|uv\.lock|sbom\.json)"
REVIEWERS = ("icham",)
REFRESH_MS = 6 * 3_600_000


def law() -> dict:
    return {"format": "standard-client/1", "floors": floors_digest(),
            "bindings": {"owner": "icham", "inventory_source": "scanner", "scanner": "scanner",
                         "compliance_officer": "second"}, "targets": []}


GRANTS = [
    {"holder": "agent", "actions": ["effect:remediate"], "resources": REMEDIATE, "conditions": ["remediate-autonomous"]},
    {"holder": "agent", "actions": ["effect:remediate"], "resources": REMEDIATE, "conditions": ["remediate-reviewed"]},
    {"holder": "agent", "actions": ["observe", "certify:unknown"], "resources": REMEDIATE, "conditions": []},
    {"holder": "scanner", "actions": ["observe", "certify:real", "evidence", "reconcile"], "resources": ["repo:*"],
     "conditions": []},
    {"holder": "icham", "actions": ["observe", "certify:real"], "resources": REMEDIATE, "conditions": []},
    {"holder": "second", "actions": ["observe", "certify:real"], "resources": ["org:*"], "conditions": []},
]


def grant_of(s, holder, action, condition=None):
    for g in s["grants"].values():
        if (g["holder"] == holder and g["id"] not in s["revoked"] and g["not_after"] > s["last_at"]
                and action in g["actions"] and (condition is None or list(g["conditions"]) == [condition])):
            return g["id"]
    raise SystemExit(f"{holder} holds no active grant for {action} {condition or ''}")


def observe(node: Node, author, resource, prop, status, level="real", force=False) -> int:
    """Sign a fact when it changed, went stale, or must be seen again (force): facts are evidence, not a pulse."""
    s = node.state
    last = s["observations"].get(f"{resource}|{prop}|{author}")
    if not force and last and last["status"] == status and node.now() - last["at"] < REFRESH_MS:
        return 0
    node.add("observation", author, under=grant_of(s, author, "observe"), resource=resource, property=prop,
             status=status, level=level)
    return 1


# ---- roles ----------------------------------------------------------------------------------------------------
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


def subject_facts(world, subject) -> dict:
    """What may be believed about one declared commit, asked about that commit only."""
    pull = world.pull(subject.pr)
    if pull["head"] != subject.head or pull["base"] != "main" or not pull["same_repo"]:
        state = "moved"                                     # no longer this commit into main: another subject
    else:
        state = "merged" if pull["merged"] else lifecycle.OPEN if pull["open"] else "closed"
    conclusion = world.ci(subject.head)
    files = world.files(subject.pr)
    scope = ("dependencies" if files and len(files) == pull["changed"]
             and all(re.fullmatch(DEPENDENCY_FILES, f) for f in files) else "code")
    return {"state": state, "ci": "green" if conclusion == "success" else conclusion or "pending", "scope": scope}


def scanner_step(node: Node, world, act) -> int:
    sub = act.subject
    if act.verb == "observe":
        it, written = lifecycle.latest_intent(node.state, sub), 0
        for prop, status in subject_facts(world, sub).items():
            # after a failure, whether the pull request is still open must be seen again to be believed
            stale = prop == "state" and it is not None and lifecycle.facts(node.state, sub).get(
                "state", (None, -1))[1] <= it["stmt"]["at"]
            written += observe(node, "scanner", sub.resource, prop, status, force=stale)
        return written
    landed = subject_facts(world, sub)["state"] == "merged"
    if act.verb == "reconcile":
        node.add("reconciliation", "scanner", under=grant_of(node.state, "scanner", "reconcile"), intent=act.intent,
                 result="applied" if landed else "not_applied")
        return 1
    if act.verb == "prove" and landed:
        node.add("evidence", "scanner", under=grant_of(node.state, "scanner", "evidence"), resource=sub.resource,
                 subject=act.intent, level="real")
        return 1
    return 0


def cmd_scan(node: Node, a, world=None):
    from ops.world import GitHub
    world = world or GitHub(a.repo, os.environ["GITHUB_TOKEN"])
    node.checkpoint()
    statuses = probes.measure_all(Path(a.checkout), world, TARGETS)
    written = sum(observe(node, "scanner", TARGETS[t]["resource"], TARGETS[t]["property"], st)
                  for t, st in statuses.items())
    covered = not any(st.startswith("uncovered") for st in statuses.values())
    written += observe(node, "scanner", "repo:inventory:all", "coverage", "complete" if covered else "partial")
    for _ in range(len(lifecycle.NEXT)):                       # until the scanner's part of the automaton is still
        step = sum(scanner_step(node, world, act) for act in lifecycle.plan(node.state, node.now(), REVIEWERS)
                   if act.role == "scanner")
        written += step
        if not step:
            break
    node.retain()
    print(json.dumps({"measured": statuses, "written": written}))


def cmd_agent(node: Node, a, world=None, craft=agent.craft):
    from ops.world import GitHub
    asked = []
    for act in lifecycle.plan(node.state, node.now(), REVIEWERS):
        if act.role == "agent" and act.verb == "ask":
            retry = {"retry_of": act.intent} if act.intent else {}
            try:
                node.add("intent", "agent", under=grant_of(node.state, "agent", "effect:remediate", act.condition),
                         op="remediate", args=act.subject.args, **retry)
                asked.append(act.subject.pr)
            except Refused as r:
                print(f"#{act.subject.pr}: {r.code} {r.detail}")
    node.retain()
    # Then at most one new repair: the most urgent repairable gap that no live declared commit already addresses.
    s = node.state
    live = {(x.area, x.item) for x in lifecycle.declared(s)
            if lifecycle.facts(s, x).get("state", (lifecycle.OPEN,))[0] == lifecycle.OPEN}
    gaps = sorted((TARGETS[t]["due_ms"], t) for t in agent.WRITE_SCOPE
                  if probes.repairable(s["observations"].get(
                      f"{TARGETS[t]['resource']}|{TARGETS[t]['property']}|scanner", {}).get("status", ""))
                  and tuple(TARGETS[t]["resource"].split(":")[1:]) not in live)
    proposed = None
    if gaps:
        t = TARGETS[gaps[0][1]]
        _, area, item = t["resource"].split(":")
        status = s["observations"][f"{t['resource']}|{t['property']}|scanner"]["status"]
        repair = craft(Path(a.checkout), t["id"], status, os.environ.get("ANTHROPIC_API_KEY", ""))
        world = world or GitHub(a.repo, os.environ["AGENT_GITHUB_TOKEN"])
        pr = world.propose(agent.branch_for(area, item), repair["files"], repair["title"],
                           f"{repair['body']}\n\n---\nStandard target `{t['id']}` read `{status}`. This commit merges "
                           "only through the law: green CI and dependency-only scope, or a signed human review.")
        resource = f"repo:{area}:{item}/pr/{pr['number']}/{pr['head']}"
        observe(node, "agent", resource, "proposed", "open", level="unknown")
        proposed = resource
    node.retain()
    print(json.dumps({"asked": asked, "proposed": proposed}))


def cmd_guard(node: Node, a, port=None):
    from adapters.github import GitHub
    port = port or EffectPort(GitHub(a.repo, os.environ["MERGE_TOKEN"]).ports())
    guard = Guard(node.journal, "guard", node.signer("guard"), port)
    results = {}
    for act in lifecycle.plan(node.state, node.now(), REVIEWERS):
        if act.role != "guard":
            continue
        try:
            if act.verb == "issue":
                guard.issue(act.intent, node.now())
            token = node.state["token_of"][act.intent]
            guard.redeem(token, node.now())
            results[act.intent] = node.state["executed"].get(token)
        except Refused as r:
            results[act.intent] = f"refused {r.code}"
    node.retain()
    print(json.dumps(results))


def cmd_review(node: Node, a):
    """A human approves one declared commit, with their own key: the review is a signed fact, not a GitHub record."""
    node.checkpoint()
    subject = next((x for x in lifecycle.declared(node.state) if x.pr == a.pr), None)
    if subject is None:
        raise SystemExit(f"#{a.pr} is not a commit the agent declared")
    observe(node, a.reviewer, subject.resource, "review", "approved", force=True)
    node.retain()


def cmd_attest(node: Node, a):
    node.checkpoint()
    resource, prop, status = (("org:controls:soa", "coverage", "complete") if a.resource == "org:controls:soa"
                              else (a.resource, "attested", "current"))
    observe(node, "second", resource, prop, status, force=True)
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
              "not_merged": sum(1 for v in s["executed"].values() if v != "ok"),
              "intents": len(s["intents"]), "proven": len(health["proven"]),
              "open": len(health["open"]), "escalated": len(health["escalated"]),
              "lines": {k: sum(1 for x in lines if x["state"] == k) for k in {x["state"] for x in lines}},
              "frameworks": {f["id"]: f["counts"] for f in dossier["frameworks"]}}
    (out / "status.json").write_text(json.dumps(status, ensure_ascii=False, indent=1))
    print(json.dumps(status, ensure_ascii=False))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m ops")
    ap.add_argument("command", choices=["init", "activate", "scan", "agent", "guard", "review", "attest", "report"])
    ap.add_argument("--state", required=True)
    ap.add_argument("--keys", help="JSON key file; default: STANDARD_KEYS")
    ap.add_argument("--publics")
    ap.add_argument("--days", type=int, default=90)
    ap.add_argument("--repo")
    ap.add_argument("--checkout", default=".")
    ap.add_argument("--pr")
    ap.add_argument("--reviewer", default="icham", choices=REVIEWERS)
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
