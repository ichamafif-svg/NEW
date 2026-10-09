"""Run exactly the historical main test files twice: baseline and shadow vNext.

A shadow intercepts ALL Kernel.decide invocations (including refusals). It
returns the original result to the test, comparing the vNext decision against
the original instead of changing the original test's behavior.

Limitations: identical application logic is currently reused by vNext, so
parity is a regression gate, NOT independent proof of the claimed guarantees.
Tests that bypass Kernel.decide are only baseline regression tests.
"""
from __future__ import annotations

import contextvars
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUITES = [
    "test_kernel.py", "test_effects.py", "test_accountability.py",
    "test_robustness.py", "test_isolation.py", "test_review.py",
    "test_floor.py", "test_language.py", "test_merge_regressions.py",
    "test_v0.py", "test_floors.py", "test_v6.py", "test_maintenance.py",
    "test_budget_classification.py", "test_root_causes.py", "test_m2.py",
    "test_compliance.py", "test_ops.py", "test_m2_review.py",
]
IN_SHADOW = contextvars.ContextVar("vnext_shadow", default=False)
COUNTS = {"compared": 0, "accepted": 0, "refused": 0, "disagreements": []}


def _delta_bytes(delta):
    from tcb.canon import canon
    return canon([list(op) for op in delta])


def install_shadow():
    """Keep baseline semantics while checking every intercepted verdict."""
    from tcb.kernel import Kernel, Refused
    from vnext import DeterministicCore
    from tcb.canon import canon

    baseline_decide = Kernel.decide
    core = DeterministicCore()

    def judge(self, state, entry):
        if IN_SHADOW.get():
            return baseline_decide(self, state, entry)
        token = IN_SHADOW.set(True)
        try:
            try:
                accepted = baseline_decide(self, state, entry)
                baseline_error = None
            except Refused as exc:
                accepted = None
                baseline_error = exc
            try:
                observed = core.evaluate(state, entry)
                shadow_error = None
            except Exception as exc:  # diagnose any non-Refused failure too
                observed = None
                shadow_error = exc
            COUNTS["compared"] += 1
            mismatch = None
            if baseline_error is not None:
                COUNTS["refused"] += 1
                if not isinstance(shadow_error, Refused) or shadow_error.code != baseline_error.code:
                    mismatch = {"expected": baseline_error.code,
                                "vnext": getattr(shadow_error, "code", type(shadow_error).__name__ if shadow_error else "accepted")}
            else:
                COUNTS["accepted"] += 1
                if shadow_error is not None:
                    mismatch = {"expected": "ADMITTED", "vnext": getattr(shadow_error, "code", type(shadow_error).__name__)}
                elif (canon(accepted[0]) != observed.record_bytes
                      or _delta_bytes(accepted[1]) != observed.delta_bytes):
                    mismatch = {"expected": "same record and ordered delta", "vnext": "different transition"}
            if mismatch is not None:
                COUNTS["disagreements"].append({"seq": entry.get("seq") if isinstance(entry, dict) else None,
                                                 **mismatch})
            if baseline_error is not None:
                raise baseline_error
            return accepted
        finally:
            IN_SHADOW.reset(token)

    Kernel.decide = judge


def child(test: str):
    if os.getenv("STANDARD_VNEXT_SHADOW") == "1":
        install_shadow()
    import runpy
    try:
        runpy.run_path(str(ROOT / "tests" / test), run_name="__main__")
    finally:
        if os.getenv("STANDARD_VNEXT_SHADOW") == "1":
            print("VNEXT_SHADOW_JSON=" + json.dumps(COUNTS, sort_keys=True))


def suite(test, shadow):
    env = dict(os.environ, STANDARD_VNEXT_SHADOW="1" if shadow else "0")
    proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--child", test],
                          cwd=ROOT, env=env, capture_output=True, text=True, timeout=240)
    passes = len(re.findall(r"(?m)^PASS\s+", proc.stdout))
    marker = next((x.split("=", 1)[1] for x in proc.stdout.splitlines()
                   if x.startswith("VNEXT_SHADOW_JSON=")), None)
    report = json.loads(marker) if marker else {}
    return {"exit": proc.returncode, "passes": passes,
            "compared": report.get("compared", 0), "accepted": report.get("accepted", 0),
            "refused": report.get("refused", 0),
            "disagreements": report.get("disagreements", []),
            "stderr_tail": proc.stderr[-900:] if proc.returncode else "",
            "stdout_tail": proc.stdout[-900:] if proc.returncode else ""}


def main():
    results = []
    for test in SUITES:
        base = suite(test, False)
        shadow = suite(test, True)
        ok = (base["exit"] == shadow["exit"] == 0 and
              base["passes"] == shadow["passes"] and
              not shadow["disagreements"])
        results.append({"test": test, "baseline": base, "vnext_shadow": shadow, "parity": ok})
        print(f"{'PASS' if ok else 'FAIL'} {test} original={base['passes']} vnext={shadow['passes']}"
              f" compared={shadow['compared']} divergent={len(shadow['disagreements'])}", flush=True)
    result = {
        "baseline_commit": "d6347dccec714c0193bbc43af5de7e96e3a9ad27",
        "kind": "same-test differential shadow, inherited runtime",
        "results": results,
        "all_parity": all(r["parity"] for r in results),
        "total_intercepted": sum(r["vnext_shadow"]["compared"] for r in results),
        "total_disagreements": sum(len(r["vnext_shadow"]["disagreements"]) for r in results),
    }
    output = ROOT / "validation" / "vnext-differential.json"
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(f"REPORT {output.relative_to(ROOT)}", flush=True)
    if not result["all_parity"] or not result["total_intercepted"]:
        return 1
    return 0


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--child":
        child(sys.argv[2])
    else:
        sys.exit(main())
