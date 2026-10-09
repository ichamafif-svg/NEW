"""Totality, bounded evaluation and cost: malformed input is refused (never a crash, never an admission), a condition
cannot burn unbounded work, and a write costs one decision whatever the journal's length."""
import base64
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixture import DAY, T0, Refused, World, copy, run  # noqa: E402
from tcb.policy import MAX_FACTS, PolicyError, validate, evaluate  # noqa: E402
from tcb.ledger import entry  # noqa: E402
from tcb import Accountability  # noqa: E402
from tcb.sign import envelope  # noqa: E402
from tcb.crypto import keyid  # noqa: E402
from fixture import public  # noqa: E402


def test_malformed_entries_are_refusals():
    w = World()
    s = w.state
    good, _ = w.signed("freeze", "sentinel", T0 + 1, scope="repo:x:*")
    env = good["envelope"]
    mutants = [None, {}, {"seq": 1}, entry(s["size"], s["head"], None), entry(s["size"], s["head"], {"payloadType": 1}),
               entry(s["size"], s["head"], {**env, "payload": 7}), entry(s["size"], s["head"], {**env, "signatures": [1]}),
               entry(s["size"], s["head"], {**env, "payload": base64.b64encode(b'{"\\ud800":1}').decode()}),
               entry(s["size"], s["head"], {**env, "payload": base64.b64encode(b"9" * 5000).decode()})]
    rng = random.Random(7)
    raw = bytearray(base64.b64decode(env["payload"]))
    for _ in range(200):
        m = bytearray(raw)
        i = rng.randrange(len(m))
        m[i] = (m[i] + 1 + rng.randrange(255)) % 256                # always a different byte
        mutants.append(entry(s["size"], s["head"], {**env, "payload": base64.b64encode(bytes(m)).decode()}))
    for bad in mutants:
        try:
            w.kernel.decide(s, bad)
        except Refused:
            continue
        raise AssertionError(f"admitted {bad!r:.80}")
    for root in ({"threshold": 2, "identities": {"a": "x"}}, {"threshold": "2", "identities": {}},
                 {"threshold": 2, "identities": {"a": {"kind": "human", "keys": [{"alg": "ed25519", "public": "%%"}]}}}):
        w.refuse("TYPE.ROOT", "rotate", "alice", T0 + 2, ["alice", "bob"], root=root)
    w.refuse("TYPE.SHAPE", "grant", "alice", T0 + 3, ["alice", "bob"], holder="agent", actions=["effect:merge"],
             resources=["repo:pr:*"], conditions=[], budget={"count": "1"}, not_after=T0 + DAY)


def test_condition_work_is_bounded():
    started = time.time()
    try:
        evaluate(validate({"all": [{"closed_at_least": ["workitem", 2]}]}), request={},
                 closed=[("workitem", str(i)) for i in range(MAX_FACTS + 1)])
        raise AssertionError("an excessive fact set was accepted")
    except PolicyError:
        pass
    assert time.time() - started < 2
    w = World()
    gid, t = w.grant("agent", ["effect:merge"], ["repo:pr:*"], T0 + 1)
    bomb = [{"head": ["p", ["?a", "?b", "?c", "?d"]], "body": [["rank", ["?a", "?x"]], ["stmt", ["?b", "?y"]],
                                                              ["stmt", ["?c", "?z"]], ["stmt", ["?d", "?u"]]]},
            {"head": ["ok", []], "body": [["p", ["?a", "?b", "?c", "?d"]], ["p", ["?d", "?c", "?b", "?a"]]]}]
    w.refuse("LAW.CONDITION", "delegate", "agent", t, parent=gid, holder="agent", actions=["effect:merge"],
             resources=["repo:pr:*"], conditions=[{"rules": bomb}], not_after=T0 + 20 * DAY)


def test_write_cost_is_flat_in_journal_length():
    w = World()
    costs = []
    t = T0
    for i in range(1, 1201):
        t += 1
        t0 = time.perf_counter()
        w.add("heartbeat", "sentinel", t, seen=0)
        costs.append(time.perf_counter() - t0)
        if i % 250 == 0:
            t += 1
            w.tick(t)
    first, last = sum(costs[:100]) / 100, sum(costs[-100:]) / 100
    assert last < 4 * first + 0.002, (first, last)
    reopened = w.other_journal()
    t0 = time.perf_counter()
    reopened.snapshot()                                           # one full verification on open
    assert reopened.state["head"] == w.state["head"]
    print(f"     write ~{last * 1000:.1f} ms at {w.state['size']} entries; full replay {time.perf_counter() - t0:.2f}s")


def test_tampered_tip_forces_full_replay_and_rollback_is_detected():
    import sqlite3
    w = World()
    w.add("freeze", "sentinel", T0 + 1, scope="repo:x:*")
    s = copy.deepcopy(w.state)
    w.pins.retain({"size": s["size"], "head": s["head"]})
    db = sqlite3.connect(w.path)
    db.execute("DELETE FROM entries WHERE seq = ?", (s["size"] - 1,))
    db.commit()
    try:
        w.journal.snapshot()
        raise AssertionError("a truncated journal was accepted")
    except ValueError as exc:
        assert "truncated" in str(exc)


def test_accountability_and_external_reader_cannot_mutate_kernel_state():
    w = World()
    original = w.state["root"]["threshold"]
    try:
        w.state["root"]["threshold"] = 1
        raise AssertionError("a snapshot was writable")
    except TypeError:
        pass

    class BrokenAccountability(Accountability):
        def feed(self, a, ks, record):
            ks["root"]["threshold"] = 1

    w.journal.accountability = BrokenAccountability(w.kernel)
    w.add("heartbeat", "sentinel", T0 + 1, seen=0)
    assert w.state["root"]["threshold"] == original
    assert w.journal.health()["state"] == "IN_PROGRESS"


def test_release_snapshot_does_not_follow_caller_mutation():
    w = World()
    old = w.kernel.law_of(w.state).release["targets"][1]["expect"]
    w.law["targets"][0]["expect"] = "red"
    assert w.kernel.law_of(w.state).release["targets"][1]["expect"] == old


def test_retained_reservation_blocks_rollback_and_failed_pin_blocks_effect():
    import sqlite3
    w = World()
    gid, at = w.grant("agent", ["effect:merge"], ["repo:pr:*"], T0 + 1)
    iid = w.add("intent", "agent", at, under=gid, op="merge", args={"pr": "42", "method": "ok"})
    calls = []
    guard = w.guard(lambda *_: calls.append(1) or "ok")
    token = guard.issue(iid, at + 1)
    token_id = next(k for k, v in w.state["tokens"].items() if v["intent"] == iid)
    guard.redeem(token_id, at + 2)
    assert len(calls) == 1
    pin = w.pins.load()[-1]
    with sqlite3.connect(w.path) as db:
        db.execute("DELETE FROM entries WHERE seq >= ?", (pin["size"] - 1,))
    try:
        w.other_journal().snapshot()
        raise AssertionError("the reservation rolled back unnoticed")
    except ValueError as exc:
        assert "retained checkpoint mismatch" in str(exc)

    w2 = World()
    gid, at = w2.grant("agent", ["effect:merge"], ["repo:pr:*"], T0 + 1)
    iid = w2.add("intent", "agent", at, under=gid, op="merge", args={"pr": "42", "method": "ok"})
    guard = w2.guard(lambda *_: calls.append(1) or "ok")
    guard.issue(iid, at + 1)
    token_id = next(k for k, v in w2.state["tokens"].items() if v["intent"] == iid)
    def unavailable(_):
        raise OSError("pin store unavailable")
    w2.pins.retain = unavailable
    try:
        guard.redeem(token_id, at + 2)
        raise AssertionError("execution without a retained pin")
    except OSError:
        pass
    assert len(calls) == 1
    assert f"reconcile:{iid}" not in w2.state["obligations"]
    assert f"unredeemed:{token_id}" in w2.state["obligations"]


def test_same_journal_serializes_concurrent_writers():
    w = World()
    initial = w.state["size"]
    def append(i):
        def build(s):
            body = {"id": f"heartbeat-parallel-{i}", "author": "sentinel",
                    "at": s["last_at"] + 1, "seen": s["size"]}
            signer = (keyid(public(w.keys["sentinel"])), w.keys["sentinel"])
            return entry(s["size"], s["head"], envelope(s["domain"], "heartbeat", body, [signer]))
        w.journal.transact(build)
    with ThreadPoolExecutor(max_workers=6) as pool:
        list(pool.map(append, range(40)))
    assert w.state["size"] == initial + 40
    assert w.other_journal().snapshot()["head"] == w.state["head"]


if __name__ == "__main__":
    run(globals())
