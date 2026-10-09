"""TCB lab G1: probe observable decisions against the inherited main kernel.

These are *scope-discovery probes*, not an abstraction or a new implementation.
Each run uses main's signed fixtures and is explicitly reported as local-only.
"""
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT))

from fixture import T0, H, World  # noqa: E402
from tcb.kernel import Refused, Kernel  # noqa: E402
from tcb.canon import canon  # noqa: E402


def record(name, experiment):
    try:
        observation = experiment()
        return {"id": name, "outcome": "observed", "observation": observation}
    except Exception as error:
        return {"id": name, "outcome": "error", "error": type(error).__name__,
                "detail": str(error)[:500]}


def restrictive_same_instant():
    w = World()
    before = w.state
    at = before["last_at"]
    first = w.add("freeze", "carol", at, scope="repo:prod:*")
    second = w.add("freeze", "alice", at, scope="repo:stage:*")
    after = w.state
    return {"accepted_at_same_instant": True,
            "frozen_count": len(after["frozen"]), "entries": [first, second],
            "scope": "local signed journal; no cross-host concurrency"}


def unsigned_mutation_has_no_effect_on_input():
    w = World()
    state = copy.deepcopy(w.state)
    entry, _ = w.signed("freeze", "carol", T0 + 1, scope="repo:prod:*")
    before = canon(state)
    record, delta = w.kernel.decide(state, entry)
    return {"state_unmodified": canon(state) == before,
            "delta_ops": [x[0] for x in delta],
            "record_kind": record["kind"],
            "scope": "pure kernel call, not physical admission"}


def wrong_authority_refused():
    w = World()
    entry, _ = w.signed("freeze", "agent", T0 + 1, scope="repo:prod:*")
    allowed, code, _ = w.kernel.admit(w.state, entry)
    return {"allowed": allowed, "refusal_code": code,
            "scope": "one signed case, not universal proof"}


def delayed_widening_requires_activation():
    w = World()
    proposal = w.add("grant", "alice", T0 + 1, ["alice", "bob"],
                     holder="agent", actions=["observe"], resources=["repo:*"],
                     conditions=[], not_after=T0 + 7 * 86_400_000)
    pending = proposal in w.state["proposals"] and proposal not in w.state["grants"]
    w.tick(T0 + H + 2)
    not_auto_activated = proposal not in w.state["grants"]
    w.add("activate", "alice", T0 + H + 3, ["alice", "bob"], proposal=proposal)
    return {"pending_before_witness": pending, "time_did_not_activate": not_auto_activated,
            "explicit_activation": proposal in w.state["grants"],
            "scope": "local signing identities in fixture"}


EXPERIMENTS = (
    ("G02_RESTRICTION_SAME_TIMESTAMP", restrictive_same_instant),
    ("G04_KERNEL_DECISION_NO_MUTATION", unsigned_mutation_has_no_effect_on_input),
    ("G01_UNAUTHORIZED_RESTRICTION", wrong_authority_refused),
    ("G01_G06_WIDENING_NOT_AUTOMATIC", delayed_widening_requires_activation),
)


def main():
    result = {"baseline": "main@d6347dccec714c0193bbc43af5de7e96e3a9ad27",
              "scope": "local decision/protocol probes only",
              "experiments": [record(name, run) for name, run in EXPERIMENTS]}
    print(json.dumps(result, indent=2))
    return 1 if any(x["outcome"] == "error" for x in result["experiments"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
