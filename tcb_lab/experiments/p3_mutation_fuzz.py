"""TCB laboratory P3: broad mutation attacks on signed constitutional admission.

Only ephemeral World fixtures and main's real Kernel. Each case records a
bounded adversarial mutation and a precise safety oracle. No real provider.
Passing means only the concrete forged entry was rejected, not formal proof.

Run: python tcb_lab/experiments/p3_mutation_fuzz.py
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
from fixture import T0, World  # noqa: E402
from tcb.canon import canon, parse  # noqa: E402

RESULTS = []


def execute(ident, family, mutate):
    w = World()
    entry, _ = w.signed("freeze", "carol", T0 + 1, scope="repo:prod:*")
    before = copy.deepcopy(w.state)
    try:
        altered = mutate(copy.deepcopy(entry), w)
        accepted, reason, _ = w.kernel.admit(w.state, altered)
        assert w.state == before, "admission mutated caller state"
        if accepted:
            outcome = "VIOLATION_OBSERVED"
            detail = "malformed or forged signed entry admitted"
        else:
            outcome = "REFUTED_UNDER_ASSUMPTIONS"
            detail = reason
    except Exception as exc:
        outcome, detail = "INCONCLUSIVE", type(exc).__name__ + ": " + str(exc)[:160]
    RESULTS.append({"id": ident, "family": family, "status": outcome, "observation": detail})


def alter_body(e, transform):
    payload = base64.b64decode(e["envelope"]["payload"])
    statement = parse(payload)
    transform(statement["predicate"])
    e["envelope"]["payload"] = base64.b64encode(canon(statement)).decode()
    return e


def alterations():
    # The default valid reference is a single human-signed restriction.
    # Every mutation below must be refused, for an independently stated reason.
    mutations = [
        ("seq-negative", "history", lambda e, w: {**e, "seq": -1}),
        ("seq-future", "history", lambda e, w: {**e, "seq": e["seq"] + 9}),
        ("seq-bool", "history", lambda e, w: {**e, "seq": True}),
        ("seq-text", "history", lambda e, w: {**e, "seq": str(e["seq"])}),
        ("prev-empty", "history", lambda e, w: {**e, "prev": ""}),
        ("prev-foreign", "history", lambda e, w: {**e, "prev": "sha256:" + "0" * 64}),
        ("entry-extra", "history", lambda e, w: {**e, "bypass": True}),
        ("entry-missing-seq", "history", lambda e, w: {k: v for k, v in e.items() if k != "seq"}),
        ("entry-null", "history", lambda e, w: None),
        ("entry-array", "history", lambda e, w: []),
        ("envelope-empty", "envelope", lambda e, w: {**e, "envelope": {}}),
        ("envelope-null", "envelope", lambda e, w: {**e, "envelope": None}),
        ("envelope-extra", "envelope", lambda e, w: {**e, "envelope": {**e["envelope"], "trust": "me"}}),
        ("payload-type", "envelope", lambda e, w: {**e, "envelope": {**e["envelope"], "payloadType": "text/plain"}}),
        ("payload-garbage", "envelope", lambda e, w: {**e, "envelope": {**e["envelope"], "payload": "!!"}}),
        ("payload-rewrite-scope", "signature", lambda e, w: alter_body(e, lambda b: b.update(scope="repo:all:*"))),
        ("payload-rewrite-time", "signature", lambda e, w: alter_body(e, lambda b: b.update(at=T0 + 2))),
        ("payload-rewrite-author", "signature", lambda e, w: alter_body(e, lambda b: b.update(author="alice"))),
        ("payload-rewrite-id", "signature", lambda e, w: alter_body(e, lambda b: b.update(id="different"))),
        ("signatures-empty", "signature", lambda e, w: {**e, "envelope": {**e["envelope"], "signatures": []}}),
        ("signatures-duplicate", "signature", lambda e, w: {**e, "envelope": {**e["envelope"], "signatures": e["envelope"]["signatures"] * 2}}),
        ("signatures-wrong-keyid", "signature", lambda e, w: {**e, "envelope": {**e["envelope"], "signatures": [{**e["envelope"]["signatures"][0], "keyid": "sha256:" + "f" * 64}]}}),
        ("signatures-zeroed", "signature", lambda e, w: {**e, "envelope": {**e["envelope"], "signatures": [{**e["envelope"]["signatures"][0], "sig": base64.b64encode(bytes(64)).decode()}]}}),
        ("signatures-extra-field", "signature", lambda e, w: {**e, "envelope": {**e["envelope"], "signatures": [{**e["envelope"]["signatures"][0], "trust": True}]}}),
        ("signatures-not-list", "signature", lambda e, w: {**e, "envelope": {**e["envelope"], "signatures": "alice"}}),
        ("signed-extra-body", "shape", lambda e, w: alter_body(e, lambda b: b.update(admin=True))),
        ("signed-missing-body", "shape", lambda e, w: alter_body(e, lambda b: b.pop("scope", None))),
        ("signed-negative-time", "time", lambda e, w: alter_body(e, lambda b: b.update(at=-1))),
        ("signed-time-way-ahead", "time", lambda e, w: alter_body(e, lambda b: b.update(at=T0 + 10**12))),
        ("signed-bool-time", "time", lambda e, w: alter_body(e, lambda b: b.update(at=True))),
    ]
    for idx, (name, family, fn) in enumerate(mutations, 1):
        execute(f"P3-M{idx:02d}", family, fn)


def main():
    alterations()
    print(json.dumps({"reference": "main@d6347dc", "kind": "isolated signed-entry mutation",
                      "total": len(RESULTS), "attacks": RESULTS}, indent=2))
    return int(any(r["status"] != "REFUTED_UNDER_ASSUMPTIONS" for r in RESULTS))


if __name__ == "__main__":
    raise SystemExit(main())
