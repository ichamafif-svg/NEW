"""Standard maintenance, one role per command. A role holds only its own keys and acts only on what the journal names.

  init      humans: genesis (root + client law) and the grant proposals
  activate  humans: activate proposals whose witnessed delay has elapsed
  witness   witnesses: sign the journal's head at real time (each writing job starts with it)
  measure   no key: measure main, and the applicability and reproducibility of declared transitions -> JSON
  test      no key: run main's test suite on main and on declared heads -> JSON (the only place code runs)
  scan      scanner: sign what measure and test found; reconcile and prove effects
  agent     agent: ask for ready transitions, withdraw dead ones, build and declare at most one new repair
  guard     guard: token, durable reservation, rejudgment, fast-forward through the trusted adapter
  review    a human: approve one declared transition, named by its head commit
  attest    the compliance officer: attest an organisational measure
  report    anyone: health, work plan, compliance dossier, status

The rules these roles follow are stated in ops/lifecycle.py, ops/world.py, ops/probes.py, ops/recipes.py and
ops/testrun.py, and checked as properties by tests/test_m2_review.py."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tcb import EffectPort, Guard, Refused  # noqa: E402
from tcb.floors import FLOORS, floors_digest  # noqa: E402

from ops import agent, lifecycle, probes, recipes  # noqa: E402
from ops.node import HUMANS, Node, load_keys, root_of  # noqa: E402

DAY = 86_400_000
TARGETS = {t["id"]: t for t in FLOORS["targets"]}
BY_RESOURCE = {tuple(t["resource"].split(":")[1:]): t["id"] for t in FLOORS["targets"] if t.get("repair") == "remediate"}
REMEDIATE = ["repo:deps:*", "repo:code:*", "repo:ci:*", "repo:supply:*"]
REVIEWERS = ("icham",)
REFRESH_MS = 6 * 3_600_000
ATTEMPT_BACKOFF_MS = DAY


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


def judged(s) -> set:
    """Heads main may legitimately contain: those of effects the law admitted and that landed."""
    return {it["args"]["head"] for i, it in s["intents"].items()
            if it["op"] == "remediate" and s["line"].get(i, {}).get("state") == "proving"}


def anchor(s):
    o = s["observations"].get("repo:main:anchor|sha|scanner")
    return o["status"] if o else None


def to_measure(node: Node) -> list:
    return [a.subject for a in lifecycle.plan(node.state, node.now(), REVIEWERS)
            if a.role == "scanner" and a.verb == "observe"]


# ---- humans and witnesses -------------------------------------------------------------------------------------
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


def cmd_witness(node: Node, a):
    node.checkpoint()
    node.retain()


def cmd_review(node: Node, a):
    """A human approves one transition, named by the head commit they read: never by a mutable pointer."""
    node.checkpoint()
    subject = next((x for x in lifecycle.declared(node.state) if x.head == a.head), None)
    if subject is None:
        raise SystemExit(f"{a.head} is not the head of a declared transition")
    observe(node, a.reviewer, subject.resource, "review", "approved", force=True)
    node.retain()


def cmd_attest(node: Node, a):
    node.checkpoint()
    resource, prop, status = (("org:controls:soa", "coverage", "complete") if a.resource == "org:controls:soa"
                              else (a.resource, "attested", "current"))
    observe(node, "second", resource, prop, status, force=True)
    node.retain()


# ---- instruments without keys ---------------------------------------------------------------------------------
def recipe_data(tree, world):
    """Trusted data recipes take: advisories for the base lock, tag resolution for actions."""
    deps = probes.audit(tree)
    return lambda target: {"vulns": probes.advisories(deps),
                           "actions": lambda repo, tag: world.tag_commit(repo, tag)}.get(target)


def transition_facts(world, subject, tree, data) -> dict:
    """Applicability and reproducibility of one declared transition, from git objects only. Any failure is a fact
    about this transition (`unanswerable`), never a stop for the others."""
    try:
        main = world.main_head()
        if main == subject.head or world.contains(subject.head, main):
            return {"state": "landed"}
        if main != subject.base or world.parents(subject.head) != [subject.base]:
            return {"state": "superseded"}
        recipe = recipes.RECIPES.get(BY_RESOURCE.get((subject.area, subject.item)))
        expected = recipe(tree, data(BY_RESOURCE[(subject.area, subject.item)])) if recipe else None
        return {"state": "open",
                "reproduced": recipes.reproduces(expected, world.tree(subject.base), world.tree(subject.head),
                                                 world.blob)}
    except Exception:  # noqa: BLE001
        return {"state": "unanswerable"}


def cmd_measure(node: Node, a, world=None, tree=None):
    from ops.world import GitHub
    world = world or GitHub(a.repo, os.environ["GITHUB_TOKEN"])
    tree = tree or probes.Checkout(a.checkout)
    s = node.state
    main = world.main_head()
    ctx = {"world": world, "main": main, "anchor": anchor(s) or main, "judged": judged(s),
           "audit": lambda: probes.audit(tree)}
    statuses = probes.measure_all(tree, ctx, TARGETS)
    try:
        data = recipe_data(tree, world)
    except Exception:  # noqa: BLE001 - without trusted data nothing is reproducible
        def data(target):
            return None
    subjects = {x.resource: transition_facts(world, x, tree, data) for x in to_measure(node)}
    out = {"main": main, "anchor": anchor(s) or main, "targets": statuses, "subjects": subjects}
    Path(a.measured).write_text(json.dumps(out, indent=1))
    print(json.dumps(out))


def fetch_heads(checkout, subjects, where: Path) -> dict:
    """A worktree per declared head; a head that cannot be fetched is left out (uncovered, never green)."""
    heads = {}
    for x in subjects:
        wt = where / f"head-{x.head[:12]}"
        try:
            subprocess.run(["git", "-C", checkout, "fetch", "-q", "origin", x.head], check=True, timeout=300)
            subprocess.run(["git", "-C", checkout, "worktree", "add", "-q", "--detach", str(wt), x.head],
                           check=True, timeout=300)
            heads[x.resource] = str(wt)
        except (subprocess.SubprocessError, OSError):
            pass
    return heads


def cmd_test(node: Node, a, run=None, fetch=fetch_heads):
    from ops import testrun
    run = run or testrun.test_all
    heads = fetch(a.checkout, to_measure(node), Path(a.tested).resolve().parent)
    out = run(Path(a.checkout), heads)
    for x in to_measure(node):
        out["subjects"].setdefault(x.resource, "uncovered:fetch")
    Path(a.tested).write_text(json.dumps(out, indent=1))
    print(json.dumps(out))


# ---- roles with keys ------------------------------------------------------------------------------------------
def scanner_step(node: Node, world, act) -> int:
    sub = act.subject
    main = world.main_head()
    landed = main == sub.head or world.contains(sub.head, main)
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
    """Sign the measures taken without keys, then settle effects. One subject's failure stays that subject's."""
    from ops.world import GitHub
    world = world or GitHub(a.repo, os.environ["GITHUB_TOKEN"])
    measured, tested = json.loads(Path(a.measured).read_text()), json.loads(Path(a.tested).read_text())
    statuses = dict(measured["targets"], ci=tested.get("main", "uncovered:missing"))
    written = 0
    if anchor(node.state) is None:
        written += observe(node, "scanner", "repo:main:anchor", "sha", measured["anchor"])
    written += observe(node, "scanner", "repo:main:measured", "sha", measured["main"])
    for t, st in statuses.items():
        written += observe(node, "scanner", TARGETS[t]["resource"], TARGETS[t]["property"], st)
    covered = not any(st.startswith("uncovered") for st in statuses.values())
    written += observe(node, "scanner", "repo:inventory:all", "coverage", "complete" if covered else "partial")
    for resource, f in measured["subjects"].items():
        sub = lifecycle.subject_of(resource)
        it = lifecycle.latest_intent(node.state, sub)
        seen_at = lifecycle.facts(node.state, sub).get("state", (None, -1))[1]
        f = dict(f, tests=tested["subjects"].get(resource, "uncovered:missing"))
        for prop in ("state", "reproduced", "tests"):
            if prop in f:      # after a failure, applicability must be seen again to be believed
                written += observe(node, "scanner", resource, prop, f[prop],
                                   force=prop == "state" and it is not None and seen_at <= it["stmt"]["at"])
    for _ in range(len(lifecycle.NEXT)):                       # the scanner's part of the automaton, to a fixpoint
        step = 0
        for act in lifecycle.plan(node.state, node.now(), REVIEWERS):
            if act.role == "scanner" and act.verb in ("reconcile", "prove"):
                try:
                    step += scanner_step(node, world, act)
                except Exception as exc:  # noqa: BLE001 - this subject waits; the others go on
                    print(f"{act.subject.head[:12]}: {type(exc).__name__}")
        written += step
        if not step:
            break
    node.retain()
    print(json.dumps({"written": written}))


def cmd_agent(node: Node, a, world=None, craft=agent.craft):
    from ops.world import GitHub
    world = world or GitHub(a.repo, os.environ["AGENT_GITHUB_TOKEN"])
    done = {"asked": [], "withdrawn": [], "proposed": None}
    for act in lifecycle.plan(node.state, node.now(), REVIEWERS):
        if act.role != "agent":
            continue
        try:
            if act.verb == "ask":
                retry = {"retry_of": act.intent} if act.intent else {}
                node.add("intent", "agent", under=grant_of(node.state, "agent", "effect:remediate", act.condition),
                         op="remediate", args=act.subject.args, **retry)
                done["asked"].append(act.subject.head)
            elif act.verb == "withdraw":
                observe(node, "agent", act.subject.resource, "proposed", "withdrawn", level="unknown", force=True)
                done["withdrawn"].append(act.subject.head)
        except Refused as r:
            print(f"{act.subject.head[:12]}: {r.code} {r.detail}")
    node.retain()
    done["proposed"] = propose(node, a, world, craft)
    node.retain()
    print(json.dumps(done))


def propose(node: Node, a, world, craft):
    """At most one new repair: the most urgent repairable gap no live transition addresses and that did not fail to be
    built recently. Write-ahead: the commit is created, then declared, then made reachable."""
    s, now = node.state, node.now()
    busy = {(x.area, x.item) for x in lifecycle.live(s, now, REVIEWERS)}
    for _, tid in sorted((TARGETS[t]["due_ms"], t) for t in agent.WRITE_SCOPE):
        t = TARGETS[tid]
        _, area, item = t["resource"].split(":")
        seen = s["observations"].get(f"{t['resource']}|{t['property']}|scanner")
        tried = s["observations"].get(f"{t['resource']}|attempt|agent")
        if (not seen or not probes.repairable(seen["status"]) or (area, item) in busy
                or (tried and tried["status"] == "failed" and now - tried["at"] < ATTEMPT_BACKOFF_MS)):
            continue
        try:
            tree = probes.Checkout(a.checkout)
            recipe = recipes.RECIPES.get(tid)
            files = (recipe(tree, recipe_data(tree, world)(tid)) if recipe else
                     craft(Path(a.checkout), tid, seen["status"], os.environ.get("ANTHROPIC_API_KEY", ""))["files"])
            files = {p: c if isinstance(c, bytes) else c.encode() for p, c in (files or {}).items()}
            if not all(agent.in_scope(tid, p) for p in files):
                raise ValueError("a repair outside its write scope")
            files = {p: c for p, c in files.items() if p not in tree.paths() or tree.read(p) != c}
            if not files:
                raise ValueError("no change repairs this gap")
            base = world.main_head()
            head = world.commit(base, files, f"standard: remediate {tid}")
            resource = f"repo:{area}:{item}/{base}/{head}"
            observe(node, "agent", resource, "proposed", "open", level="unknown", force=True)
            world.keep(head)
            return resource
        except Exception as exc:  # noqa: BLE001 - a failed attempt is a fact about this target, not a stop
            print(f"{tid}: {type(exc).__name__} {exc}")
            observe(node, "agent", t["resource"], "attempt", "failed", level="unknown", force=True)
            return None
    return None


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
    phases = [lifecycle.phase(s, x, node.now(), REVIEWERS)[0] for x in lifecycle.declared(s)]
    status = {"at": health["evaluated_at"], "state": health["state"], "size": s["size"], "head": s["head"],
              "landed": sum(1 for v in s["executed"].values() if v == "ok"), "intents": len(s["intents"]),
              "proven": len(health["proven"]), "open": len(health["open"]), "escalated": len(health["escalated"]),
              "subjects": {p: phases.count(p) for p in sorted(set(phases))},
              "frameworks": {f["id"]: f["counts"] for f in dossier["frameworks"]}}
    (out / "status.json").write_text(json.dumps(status, ensure_ascii=False, indent=1))
    print(json.dumps(status, ensure_ascii=False))


COMMANDS = ["init", "activate", "witness", "measure", "test", "scan", "agent", "guard", "review", "attest", "report"]


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m ops")
    ap.add_argument("command", choices=COMMANDS)
    ap.add_argument("--state", required=True)
    ap.add_argument("--keys", help="JSON key file; default: STANDARD_KEYS")
    ap.add_argument("--publics")
    ap.add_argument("--days", type=int, default=90)
    ap.add_argument("--repo")
    ap.add_argument("--checkout", default=".")
    ap.add_argument("--head")
    ap.add_argument("--reviewer", default="icham", choices=REVIEWERS)
    ap.add_argument("--resource")
    ap.add_argument("--measured", default="measured.json")
    ap.add_argument("--tested", default="tested.json")
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
