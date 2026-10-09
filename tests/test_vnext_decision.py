"""Checks over real signed statements from main's adversarial fixture."""
import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from vnext import DeterministicCore, StaleDecision
from tcb.kernel import Refused, empty
from tcb.canon import canon

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixture import T0, World, run


def test_deterministic_same_inputs_no_mutation():
    w = World()
    state = copy.deepcopy(w.state)
    entry, _ = w.signed("freeze", "alice", T0 + 1, scope="repo:prod:*")
    before, signed = canon(state), canon(entry)
    core = DeterministicCore()
    a = core.evaluate(state, entry)
    b = core.evaluate(state, entry)
    assert a == b
    assert canon(state) == before and canon(entry) == signed
    assert a.state["frozen"]["repo:prod:*"]
    assert a.law == state["law"]["digest"]


def test_preview_is_not_a_replayable_authorization():
    w = World()
    state = copy.deepcopy(w.state)
    entry, _ = w.signed("freeze", "alice", T0 + 1, scope="repo:prod:*")
    core = DeterministicCore()
    d = core.evaluate(state, entry)
    next_state = core.preview(state, d)
    assert next_state["size"] == state["size"] + 1
    assert not state["frozen"]
    try:
        core.preview(next_state, d)
    except StaleDecision:
        pass
    else:
        raise AssertionError("stale preview was accepted")


def test_same_refusal_as_historical_kernel():
    w = World()
    entry, _ = w.signed("freeze", "agent", T0 + 1, scope="repo:prod:*")
    try:
        DeterministicCore().evaluate(copy.deepcopy(w.state), entry)
    except Refused as error:
        assert error.code.startswith("CAP.")
    else:
        raise AssertionError("unauthorized action admitted")


def test_malformed_signed_entries_refused():
    core = DeterministicCore()
    for entry in ({}, {"seq": 0, "prev": None, "envelope": {}}):
        try:
            core.evaluate(empty(), entry)
        except (Refused, ValueError):
            pass
        else:
            raise AssertionError("malformed entry admitted")


if __name__ == "__main__":
    run(globals())
