"""The four root causes found by the V6 adversarial review, each closed by structure, never by a case:
  1 polarity is typed everywhere      a law cannot block restrictions, weaken a floor, or let time starve a restriction
  2 the effect line is one automaton  reconcile only what can no longer leave; repair the tail without the candidate
  3 identity is the signed meaning   one key one encoding, one envelope one form, a debt follows what it measures
  4 every permitting fact is labeled  no self-opened window or gate; the two judges never diverge on random walks
Scripts reproducing each original attack are in validation/adversarial/."""
import base64
import copy
import random
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cryptography.hazmat.primitives.asymmetric import ec  # noqa: E402
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat  # noqa: E402

from fixture import DAY, H, MAX_AHEAD_MS, T0, Refused, World, make_law, raises, run  # noqa: E402
from tcb import Accountability, audit  # noqa: E402
from tcb.canon import parse  # noqa: E402
from tcb.crypto import keyid  # noqa: E402
from tcb.floor0 import DISPATCH_MS  # noqa: E402
from tcb.kernel import check_root  # noqa: E402

ARGS = {"pr": "42", "method": "squash"}


def invalid_law(**over):
    w = World()
    _, t = w.grant("agent", ["effect:merge"], ["repo:pr:*"], T0 + 1)
    law = make_law(**over)
    w.refuse("LAW.INVALID", "law", "alice", t, ["alice", "bob"], release=law)


# ---- 1. polarity ----------------------------------------------------------------------------------------------------
def test_no_law_can_gate_a_restriction_a_witness_or_the_widening_protocol():
    for kind, key in (("revoke", "grant"), ("freeze", "scope"), ("veto", "proposal"), ("flag", "intent"),
                      ("checkpoint", "head"), ("activate", "proposal")):
        invalid_law(obligations=[{"id": "brake", "level": "refuse", "due_ms": DAY, "on_due": "lapse",
                                  "open": [{"kind": "observation", "key": "resource"}],
                                  "gate": [{"kind": kind, "key": key}]}])


def test_where_clauses_hold_one_representation_only():
    invalid_law(obligations=[{"id": "force-approval", "level": "refuse", "due_ms": DAY, "on_due": "lapse",
                              "open": [{"kind": "observation", "key": "resource"}],
                              "gate": [{"kind": "intent", "key": "args.pr", "where": {"args.force": True}}]}])


def test_a_client_never_proves_more_cheaply_than_the_floors():
    invalid_law(evidence={"cheap": {"fields": {"under": "id", "resource": "resource", "subject": "id", "level": "str"}}},
                discharges={"cheap": [{"obligation": "proof", "key": "subject", "min_level": "unknown"}]})


def test_a_restriction_shares_the_last_instant_when_the_ceiling_is_taken():
    w = World()
    gid, t = w.grant("agent", ["effect:merge"], ["repo:pr:*"], T0 + 1)
    ceiling = w.state["anchor_at"] + MAX_AHEAD_MS
    w.add("delegate", "agent", ceiling, parent=gid, holder="agent", actions=["effect:merge"], resources=["repo:pr:1"],
          conditions=[], not_after=ceiling + 1)
    w.add("freeze", "sentinel", ceiling, scope="repo:*")
    w.add("revoke", "carol", ceiling, grant=gid)
    w.refuse("HIST.TIME", "delegate", "agent", ceiling, parent=gid, holder="agent", actions=["effect:merge"],
             resources=["repo:pr:2"], conditions=[], not_after=ceiling + 1)


def test_unnamed_facts_cannot_crowd_out_a_condition():
    law = make_law(conditions={"ci-green": {"all": [{"observed": ["ci", "green", "real"]}]}})
    w = World(law=law)
    oid, t = w.grant("ci", ["observe", "certify:real"], ["repo:*"], T0 + 1)
    gid, t = w.grant("agent", ["effect:merge"], ["repo:pr:*"], t, conditions=["ci-green"])
    w.add("observation", "ci", t, under=oid, resource="repo:pr:42", property="ci", status="green", level="real")
    with patch("tcb.policy.MAX_FACTS", 2):
        for n in range(4):
            w.add("observation", "ci", t + 1 + n, under=oid, resource=f"repo:noise:{n}", property="x", status="y", level="real")
        w.add("intent", "agent", t + 10, under=gid, op="merge", args=ARGS)


# ---- 2. the effect line ---------------------------------------------------------------------------------------------
def test_a_reservation_is_reconciled_only_once_it_can_no_longer_leave():
    w = World()
    gid, t = w.grant("agent", ["effect:merge"], ["repo:pr:*"], T0 + 1)
    rid, t = w.grant("readback", ["reconcile"], ["repo:pr:*"], t)
    iid = w.add("intent", "agent", t, under=gid, op="merge", args=ARGS)
    calls = []
    g = w.guard(lambda *a: calls.append(a) or "ok")
    g.issue(iid, t + 1)
    tid = w.state["token_of"][iid]
    g.journal.transact(lambda s: g._entry(s, "reservation", {"id": "res-x", "at": t + 2, "token": tid}))
    w.refuse("OBL.LINE", "reconciliation", "readback", t + 3, under=rid, intent=iid, result="not_applied")
    late = t + 2 + DISPATCH_MS + 1
    w.tick(late)
    with raises(Refused, "OBL.LINE"):
        w.journal.kernel.judge_dispatch(w.journal.state, tid, "guard", late)
    w.add("reconciliation", "readback", late + 1, under=rid, intent=iid, result="not_applied")
    w.add("intent", "agent", late + 2, under=gid, op="merge", args=ARGS, retry_of=iid)
    assert calls == []


def test_an_interrupted_commit_is_repaired_from_the_kept_tail_alone():
    w = World()
    candidate, _ = w.signed("freeze", "carol", T0 + 1, scope="repo:pr:*")
    retained = w.pins.retain

    def interrupted(pin):
        retained(pin)
        raise OSError("crash after pin commit")
    with patch.object(w.pins, "retain", side_effect=interrupted):
        with raises(OSError, "crash after pin commit"):
            w.journal.append(candidate)
    del candidate                                            # nobody kept the entry
    assert "repo:pr:*" in w.journal.recover_tail()["frozen"]


# ---- 3. identity is the signed meaning ------------------------------------------------------------------------------
def test_one_passkey_is_one_key():
    k = ec.generate_private_key(ec.SECP256R1())
    w = World(genesis=False)
    root = copy.deepcopy(w.root)
    p = base64.b64encode(k.public_key().public_bytes(Encoding.X962, PublicFormat.CompressedPoint)).decode()
    root["identities"]["mallory"] = {"kind": "human", "keys": [{"alg": "webauthn-es256", "public": p, "keyid": keyid(p),
                                                                 "rp_id": "ex.org", "origins": ["https://ex.org"]}]}
    with raises(Refused, "TYPE.ROOT"):
        check_root(root)


def test_an_envelope_has_one_form():
    w = World()
    e, _ = w.signed("freeze", "carol", T0 + 1, ["carol", "dave"], scope="repo:*")
    for mutate in (lambda env: env.update(note="unsigned"),
                   lambda env: env["signatures"].reverse(),
                   lambda env: env["signatures"].append(dict(env["signatures"][0])),
                   lambda env: env["signatures"][0].update(extra="junk")):
        bad = copy.deepcopy(e)
        mutate(bad["envelope"])
        assert w.kernel.admit(w.journal.state, bad)[1] == "SIG.ENVELOPE"
    w.journal.append(e)


def test_a_renamed_target_keeps_its_debt():
    def verdict(w):
        s = w.state
        rows = [parse(r) for r in w.journal.raw_rows(0, s["size"], 10 ** 6)]
        return audit(w.kernel, Accountability(w.kernel), rows, genesis_pin=w.journal.genesis_pin,
                     checkpoints=[{"size": s["size"], "head": s["head"]}])
    due = {}
    for rename in (False, True):
        w = World()
        law = copy.deepcopy(w.law)
        if rename:
            law["targets"][0]["id"] = "renamed"
        _, t = w.widen("law", T0 + 1, release=law)
        w.tick(T0 + DAY + H)
        v = verdict(w)
        due[rename] = next(o["due"] for o in v["open"] + v["escalated"] if o["obligation"].endswith(("pr42-ci", "renamed")))
    assert due[True] == due[False], due


# ---- 4. every permitting fact is labeled ----------------------------------------------------------------------------
def window_law():
    law = make_law(conditions={"in-window": {"all": [{"open": ["change-window", "resource"]}]}})
    law["obligations"] = [{"id": "change-window", "level": "refuse", "due_ms": DAY, "on_due": "lapse",
                           "open": [{"kind": "observation", "key": "resource", "where": {"property": "window"}}]},
                          {"id": "release-gate", "level": "refuse", "due_ms": DAY, "on_due": "lapse", "reopen": "replace",
                           "open": [{"kind": "observation", "key": "status", "where": {"property": "approval"}}],
                           "gate": [{"kind": "intent", "op": "merge", "key": "args.pr", "where": {"args.method": "squash"}}]}]
    return law


def test_an_actor_never_opens_its_own_window_or_gate():
    w = World(law=window_law())
    self_obs, t = w.grant("agent", ["observe", "certify:unknown"], ["repo:*"], T0 + 1)
    ci_obs, t = w.grant("ci", ["observe", "certify:unknown"], ["repo:*"], t)
    windowed, t = w.grant("agent", ["effect:merge"], ["repo:pr:*"], t, conditions=["in-window"])
    plain, t = w.grant("agent", ["effect:merge"], ["repo:pr:*"], t)
    obs = dict(resource="repo:pr:42", level="unknown")
    w.add("observation", "agent", t, under=self_obs, property="window", status="open", **obs)
    w.add("observation", "agent", t + 1, under=self_obs, property="approval", status="42", **obs)
    w.refuse("LAW.CONDITION", "intent", "agent", t + 2, under=windowed, op="merge", args={**ARGS, "method": "rebase"})
    w.refuse("OBL.GATE", "intent", "agent", t + 3, under=plain, op="merge", args=ARGS)
    w.add("observation", "ci", t + 4, under=ci_obs, property="approval", status="42", resource="repo:pr:43", level="unknown")
    w.add("intent", "agent", t + 5, under=plain, op="merge", args=ARGS)


def test_an_evidence_kind_named_like_a_handler_cannot_halt_the_second_judge():
    law = make_law(evidence={"quorum": {"fields": {"under": "id", "resource": "resource"}},
                             "use": {"fields": {"under": "id", "resource": "resource"}}})
    w = World(law=law)
    gid, t = w.grant("readback", ["quorum", "use"], ["repo:*"], T0 + 1)
    w.add("quorum", "readback", t, under=gid, resource="repo:pr:1")
    w.add("use", "readback", t + 1, under=gid, resource="repo:pr:1")
    assert w.pins.halted() is None


def test_the_two_judges_never_diverge_on_a_random_walk():
    rnd = random.Random(7)
    law = window_law()
    law["ops"] = {"deploy": {"args": {"env": "segment", "force": "int"}, "resource": "repo:deploy:{env}", "profile": "capability"}}
    w = World(law=law)
    roles = {}
    roles["agent"], t = w.grant("agent", ["effect:merge", "effect:deploy", "observe", "certify:unknown", "evidence"],
                                ["repo:*"], T0 + 1)
    roles["ci"], t = w.grant("ci", ["observe", "certify:unknown", "certify:real"], ["repo:*"], t)
    roles["readback"], t = w.grant("readback", ["reconcile", "evidence", "observe", "certify:real"], ["repo:*"], t)
    g = w.guard(lambda *a: rnd.choice(["ok", "failed", "unknown"]))
    pr = lambda: str(rnd.randint(40, 44))
    admitted = refused = 0
    for step in range(400):
        at = w.state["last_at"] + rnd.randint(0, 3)
        try:
            choice = rnd.randrange(9)
            if choice == 0:
                who = rnd.choice(["agent", "ci", "readback"])
                w.add("observation", who, at, under=roles[who], resource=f"repo:pr:{pr()}",
                      property=rnd.choice(["window", "approval", "ci"]), status=rnd.choice([pr(), "open", "green"]),
                      level=rnd.choice(["unknown", "real"]))
            elif choice == 1:
                w.add("intent", "agent", at, under=roles["agent"], op="merge",
                      args={"pr": pr(), "method": rnd.choice(["squash", "rebase"])},
                      **({"retry_of": rnd.choice(list(w.state["intents"]))} if w.state["intents"] and rnd.random() < .3 else {}))
            elif choice == 2:
                w.add("intent", "agent", at, under=roles["agent"], op="deploy", args={"env": "prod", "force": rnd.randint(0, 1)})
            elif choice == 3 and w.state["intents"]:
                g.issue(rnd.choice(list(w.state["intents"])), at)
            elif choice == 4 and w.state["tokens"]:
                g.redeem(rnd.choice(list(w.state["tokens"])), at)
            elif choice == 5 and w.state["intents"]:
                w.add("reconciliation", "readback", at, under=roles["readback"], intent=rnd.choice(list(w.state["intents"])),
                      result=rnd.choice(["applied", "not_applied"]))
            elif choice == 6 and w.state["intents"]:
                iid = rnd.choice(list(w.state["intents"]))
                w.add("evidence", rnd.choice(["readback", "agent"]), at, under=roles[rnd.choice(["readback", "agent"])],
                      resource=w.state["intents"][iid]["resource"], subject=iid, level="real")
            elif choice == 7:
                w.tick(at + rnd.randint(1, 2 * DISPATCH_MS))
            else:
                w.add(rnd.choice(["freeze", "flag"]), "sentinel", at,
                      **({"scope": f"repo:pr:{pr()}"} if rnd.random() < .5 else {"intent": rnd.choice(list(w.state["intents"]) or ["none"])}))
            admitted += 1
        except Refused as r:
            assert not r.code.startswith("HALT"), f"step {step}: the judges diverged: {r.detail}"
            refused += 1
        except KeyError:
            refused += 1
    assert w.pins.halted() is None and admitted > 100 and refused > 20, (admitted, refused)


if __name__ == "__main__":
    run(globals())
