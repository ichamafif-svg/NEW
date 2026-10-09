"""Single-component fault probes for the merged admission boundary."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixture import H, T0, World, digest, raises, Refused, make_law, Kernel, DAY  # noqa: E402
from tcb import policy, kernel as kernel_module  # noqa: E402


def test_a_kernel_signature_fault_does_not_admit_a_forgery():
    w = World()
    signed, _ = w.signed("freeze", "carol", T0 + 1, scope="repo:pr:*")
    signed["envelope"]["signatures"][0]["sig"] = "AAAA"
    original = kernel_module.verify
    kernel_module.verify = lambda *args: True
    try:
        with raises(Refused, "HALT.DISAGREEMENT"):
            w.journal.append(signed)
    finally:
        kernel_module.verify = original
    assert w.pins.halted()


def test_a_kernel_head_fault_does_not_change_history():
    w = World()
    original = w.kernel.decide
    def changed(state, entry):
        record, delta = original(state, entry)
        delta = [("set", "head", "sha256:" + "0" * 64) if op[:2] == ("set", "head") else op for op in delta]
        return record, delta
    w.kernel.decide = changed
    with raises(Refused, "HALT.DISAGREEMENT"):
        w.add("freeze", "carol", T0 + 1, scope="repo:pr:*")
    assert w.pins.halted()


def test_a_kernel_grant_fault_does_not_widen_activated_rights():
    w = World()
    pid = w.add("grant", "alice", T0 + 1, ["alice", "bob"], holder="agent",
                actions=["effect:merge"], resources=["repo:pr:7"], conditions=[], not_after=T0 + 2 * DAY)
    w.tick(T0 + 1 + H)
    original = w.kernel._grant_record
    def broaden(body, parent, at):
        grant = original(body, parent, at)
        grant["resources"] = ["repo:*"]
        return grant
    w.kernel._grant_record = broaden
    with raises(Refused, "HALT.DISAGREEMENT"):
        w.add("activate", "alice", T0 + 2 + H, ["alice", "bob"], proposal=pid)
    assert w.pins.halted()


def test_adversarial_glob_cannot_enter_the_language():
    pattern = "*a" * 25 + "b"
    started = time.monotonic()
    with raises(policy.PolicyError, "unknown"):
        policy.validate({"all": [{"glob": ["args.pr", pattern]}]})
    assert time.monotonic() - started < 1


if __name__ == "__main__":
    from fixture import run
    run(globals())
