"""TCB phase 3 — signed-input adversarial experiments against unmodified main.

This corpus deliberately DOES NOT implement any new constitutional model.
Run from repo root: python3 tcb_lab/experiments/p3_signed_core.py
Exit nonzero on observed invariant violations or experiment setup failures.
A passing test only refutes the tested attack under its named assumptions.
"""
from __future__ import annotations

import base64
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from fixture import H, T0, World, make_law  # noqa: E402
from tcb.canon import canon  # noqa: E402
from tcb.kernel import Refused  # noqa: E402

ATTACKS = {}


def attack(ident, guarantee, assumptions):
    def decorator(fn):
        ATTACKS[ident] = (guarantee, assumptions, fn)
        return fn
    return decorator


def require_refusal(world, entry, *, reason=None):
    allowed, code, detail = world.kernel.admit(world.state, entry)
    assert not allowed, f"UNSAFE ADMISSION: {code} {detail}"
    if reason is not None:
        assert code == reason, f"unexpected refusal {code}, expected {reason}"
    return code


@attack("P3-01", "G01/G02", "attacker holds only an agent signing key")
def agent_cannot_freeze():
    w = World()
    entry, _ = w.signed("freeze", "agent", T0 + 1, scope="repo:prod:*")
    return {"refusal": require_refusal(w, entry, reason="CAP.RESTRICT")}


@attack("P3-02", "G04/G05", "the adversary may replay a signed entry but not edit journal head")
def replay_does_not_apply_twice():
    w = World()
    e, _ = w.signed("freeze", "carol", T0 + 1, scope="repo:prod:*")
    w.journal.append(e)
    after = copy.deepcopy(w.state)
    reason = require_refusal(w, e, reason="HIST.CHAIN")
    assert w.state == after
    return {"refusal": reason, "state_unchanged": True}


@attack("P3-03", "G05", "attacker changes a signed envelope without the private key")
def signature_tamper_refused():
    w = World()
    e, _ = w.signed("freeze", "carol", T0 + 1, scope="repo:prod:*")
    e = copy.deepcopy(e)
    e["envelope"]["signatures"][0]["sig"] = base64.b64encode(b"\x00" * 64).decode()
    return {"refusal": require_refusal(w, e)}


@attack("P3-04", "G01/G06", "the attacker cannot compel the required human cosigners")
def proposal_does_not_activate_automatically():
    w = World()
    pid = w.add("grant", "alice", T0 + 1, ["alice", "bob"], holder="agent",
                actions=["observe"], resources=["repo:*"], conditions=[],
                not_after=T0 + 7 * 86_400_000)
    assert pid in w.state["proposals"] and pid not in w.state["grants"]
    w.tick(T0 + H + 10)
    assert pid not in w.state["grants"], "time alone activated widening"
    entry, _ = w.signed("activate", "alice", T0 + H + 11, ["alice"], proposal=pid)
    refusal = require_refusal(w, entry)
    return {"refusal_without_quorum": refusal, "no_implicit_activation": True}


@attack("P3-05", "G02/G06", "an authorized restrictor uses the current ceiling instant")
def restrictions_can_share_timestamp():
    w = World()
    # Two independent authorized freezes at identical witness-consistent instant.
    w.add("freeze", "carol", T0 + 1, scope="repo:first:*")
    w.add("freeze", "alice", T0 + 1, scope="repo:second:*")
    assert "repo:first:*" in w.state["frozen"]
    assert "repo:second:*" in w.state["frozen"]
    return {"same_instant_restrictions": 2}


@attack("P3-06", "G07", "agent and independent observer have distinct keys and grant chains")
def self_attestation_cannot_authorize_own_intent():
    w = World(law=make_law(conditions={"ci-green": {"all": [{"observed": ["ci", "green", "real"]}]}}))
    self_obs, t = w.grant("agent", ["observe", "certify:real"], ["repo:*"], T0 + 1)
    actor, t = w.grant("agent", ["effect:merge"], ["repo:pr:*"], t, conditions=["ci-green"])
    args = {"pr": "42", "method": "squash"}
    w.add("observation", "agent", t + 1, under=self_obs, resource="repo:pr:42",
          property="ci", status="green", level="real")
    entry, _ = w.signed("intent", "agent", t + 2, under=actor, op="merge", args=args)
    refusal = require_refusal(w, entry)
    external, t = w.grant("ci", ["observe", "certify:real"], ["repo:*"], t + 3)
    w.add("observation", "ci", t + 1, under=external, resource="repo:pr:42",
          property="ci", status="green", level="real")
    assert w.kernel.admit(w.state, w.signed("intent", "agent", t + 2, under=actor, op="merge", args=args)[0])[0]
    return {"self_refusal": refusal, "independent_source_admitted": True}


@attack("P3-07", "G04", "candidate may supply malformed records, but not alter the kernel")
def malformed_entries_fail_closed():
    w = World()
    original = copy.deepcopy(w.state)
    cases = [None, [], {}, {"seq": w.state["size"], "prev": w.state["head"], "envelope": {}}]
    refused = []
    for candidate in cases:
        permitted, code, _ = w.kernel.admit(w.state, candidate)
        assert not permitted, f"malformed entry admitted: {candidate!r}"
        refused.append(code)
    assert w.state == original
    return {"refusal_codes": refused, "no_side_effect": True}


@attack("P3-08", "G01/G03", "client controls only the law declaration, not release floors")
def client_law_must_not_weaken_witnesses():
    from tcb.law import LawError
    w = World()
    law = copy.deepcopy(w.law)
    law["witnesses"] = {"quorum": 1}
    try:
        w.kernel.load(law)
    except LawError:
        return {"law_weakened": False, "refused": True}
    raise AssertionError("client law reduced witness quorum")


def run():
    entries = []
    for ident, (guarantee, assumptions, fn) in ATTACKS.items():
        try:
            evidence = fn()
            state = "REFUTED_UNDER_ASSUMPTIONS"
        except Exception as exc:
            state = "INCONCLUSIVE"
            evidence = {"error": type(exc).__name__, "message": str(exc)[:400]}
        entries.append({"id": ident, "guarantees": guarantee,
                        "assumptions": assumptions, "status": state, "evidence": evidence})
    report = {"baseline": "main@d6347dccec714c0193bbc43af5de7e96e3a9ad27",
              "scope": "local signed-kernel regression; provider and multi-host boundaries excluded",
              "attacks": entries}
    print(json.dumps(report, indent=2))
    return int(any(r["status"] == "INCONCLUSIVE" for r in entries))


if __name__ == "__main__":
    raise SystemExit(run())
