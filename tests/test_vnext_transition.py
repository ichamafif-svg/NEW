"""The transition interpreter has no knowledge of domain-specific rights or effects."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from vnext.transition import TransitionError, transition, verify


def test_complete_transition_and_trace():
    state = {"size": 1, "head": "old", "grants": {"a": {"active": True}},
             "uses": {"g": [1]}, "frozen": {"repo:*": "f-0"}}
    ops = [["set", "size", 2], ["set", "head", "new"],
           ["put", "grants", "b", {"active": True}],
           ["push", "uses", "g", 2], ["drop", "frozen", "repo:*"]]
    post, trace = transition(state, ops)
    assert post == {"size": 2, "head": "new",
                    "grants": {"a": {"active": True}, "b": {"active": True}},
                    "uses": {"g": [1, 2]}, "frozen": {}}
    assert len(trace) == len(ops)
    assert verify(state, ops, post) == trace
    assert state["size"] == 1 and "b" not in state["grants"]


def test_no_undeclared_field_changes():
    initial = {"size": 1, "rights": {"a": 1}}
    ops = [["set", "size", 2]]
    try:
        verify(initial, ops, {"size": 2, "rights": {"a": 2}})
    except TransitionError:
        pass
    else:
        raise AssertionError("unreported authority expansion accepted")


def test_closed_instruction_grammar():
    state = {"size": 0, "frozen": {}}
    malicious = (
        [["erase", "frozen", "all"]],
        [["put", "frozen", "x"]],
        [["put", "not-a-section", "x", "y"]],
        [["drop", "frozen", "absent"]],
        [["push", "size", "x", 1]],
    )
    for delta in malicious:
        try:
            transition(state, delta)
        except TransitionError:
            pass
        else:
            raise AssertionError(f"invalid mutation admitted: {delta}")


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("PASS", name)
