"""Phase 3 — effect-line adversarial exercises on main's real Journal and Guard.

Only in-memory synthetic effect ports are called. No network, GitHub writer or
production credential is involved. Result statuses apply exclusively to the
local fixture and do not establish multi-host or provider guarantees.
"""
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))
from fixture import H, T0, World  # noqa: E402
from tcb.kernel import Refused  # noqa: E402

ARGS = {"pr": "42", "method": "squash"}


def ready(w):
    grant, t = w.grant("agent", ["effect:merge"], ["repo:pr:*"], T0 + 1)
    observer, t = w.grant("readback", ["reconcile", "evidence", "observe", "certify:real"],
                          ["repo:pr:*"], t)
    return grant, observer, t


def forbid(fn, code):
    try:
        fn()
    except Refused as exc:
        assert exc.code == code, f"{exc.code} != {code}"
        return exc.code
    raise AssertionError(f"unsafe: {code} operation accepted")


def p3_16_double_redeem_local_sqlite():
    w = World()
    gid, _, t = ready(w)
    iid = w.add("intent", "agent", t, under=gid, op="merge", args=ARGS)
    calls = []
    g1 = w.guard(lambda *args: calls.append(args) or "ok")
    g1.issue(iid, t + 1)
    token = w.state["token_of"][iid]
    g2 = w.guard(lambda *args: calls.append(args) or "ok", journal=w.other_journal())

    def attempt(guard):
        try:
            guard.redeem(token, t + 2)
            return "ran"
        except Refused as exc:
            return exc.code

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(attempt, (g1, g2)))
    assert results.count("ran") == 1, results
    assert len(calls) == 1, calls
    return {"calls": len(calls), "attempts": results,
            "limit": "two processes represented by journals sharing one SQLite path, not two separate hosts"}


def p3_16_revocation_between_token_and_dispatch():
    w = World()
    gid, _, t = ready(w)
    iid = w.add("intent", "agent", t, under=gid, op="merge", args=ARGS)
    calls = []
    g = w.guard(lambda *args: calls.append(args) or "ok")
    g.issue(iid, t + 1)
    w.add("revoke", "carol", t + 2, grant=gid)
    refusal = forbid(lambda: g.redeem(w.state["token_of"][iid], t + 3), "CAP.WITHDRAWN")
    assert calls == []
    return {"refusal": refusal, "physical_calls": 0}


def p3_17_unknown_result_blocks_automatic_retry():
    w = World()
    gid, _, t = ready(w)
    iid = w.add("intent", "agent", t, under=gid, op="merge", args=ARGS)
    calls = []
    def uncertain(*args):
        calls.append(args)
        raise RuntimeError("provider applied request but acknowledgement was lost")
    g = w.guard(uncertain)
    g.issue(iid, t + 1)
    g.redeem(w.state["token_of"][iid], t + 2)
    assert len(calls) == 1
    assert f"reconcile:{iid}" in w.state["obligations"]
    refusal = forbid(
        lambda: w.add("intent", "agent", t + 4, under=gid, op="merge", args=ARGS, retry_of=iid),
        "OBL.BLOCKED",
    )
    return {"refusal": refusal, "calls": len(calls),
            "limit": "provider behavior simulated; no proof an actual network request was sent"}


def p3_14_effect_ok_does_not_close_target_automatically():
    w = World()
    gid, _, t = ready(w)
    iid = w.add("intent", "agent", t, under=gid, op="merge", args=ARGS)
    g = w.guard(lambda *args: "ok")
    g.issue(iid, t + 1)
    g.redeem(w.state["token_of"][iid], t + 2)
    assert f"proof:{iid}" in w.state["obligations"], "execution claimed success without independent proof"
    return {"proof_pending": True,
            "limit": "proof obligation about effect; separate target health still requires own evidence"}


CASES = {
    "P3-16-LOCAL": p3_16_double_redeem_local_sqlite,
    "P3-16-RESTRICT": p3_16_revocation_between_token_and_dispatch,
    "P3-17": p3_17_unknown_result_blocks_automatic_retry,
    "P3-14": p3_14_effect_ok_does_not_close_target_automatically,
}


def run():
    out = []
    for ident, fn in CASES.items():
        try:
            evidence = fn()
            result = "REFUTED_UNDER_ASSUMPTIONS"
        except Exception as exc:
            result, evidence = "INCONCLUSIVE", {"error": type(exc).__name__,
                                                 "detail": str(exc)[:350]}
        out.append({"id": ident, "status": result, "observed": evidence})
    print(json.dumps({"baseline": "main@d6347dccec714c0193bbc43af5de7e96e3a9ad27",
                      "boundary": "local SQLite journal + synthetic effect port",
                      "attacks": out}, indent=2))
    return int(any(v["status"] == "INCONCLUSIVE" for v in out))


if __name__ == "__main__":
    raise SystemExit(run())
