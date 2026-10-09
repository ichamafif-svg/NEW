"""R4b: guard runner dies between the signed reservation and the execution report (job timeout, runner lost).
The stored line state stays 'reserved'; cmd_scan compares the *stored* state with 'expired' (which only
line_state() computes), so it never reconciles, and cmd_ask never retries a non-'failed' line."""
from unittest.mock import patch

import r4_stall as base  # noqa: F401  (reuses GH; runs its own scenario first)
from harness import World, GOOD
from tcb.floor0 import line_state

gh = base.GH()
w = World(gh, measured=GOOD)
with w.env():
    w.boot()
    w.clock.t += 60
    w.step("scan")
    s = w.step("ask")
    iid = next(iter(s["intents"]))

    def die(*a, **k):
        raise KeyboardInterrupt("runner killed")
    with patch("adapters.github.GitHub.remediate", die):
        try:
            w.step("guard")
        except KeyboardInterrupt:
            pass
    for _ in range(4):
        w.clock.t += 6 * 3600
        s = w.step("scan")
        s = w.step("ask")
        w.step("guard")
    print("stored line:", s["line"][iid]["state"], "| computed:", line_state(s["line"], iid, int(w.clock.t * 1000)),
          "| reconciliations: none" if not any(k.startswith("proof:") for k in s["obligations"]) else "",
          "| open reconcile obligation:", f"reconcile:{iid}" in s["obligations"], "| merged:", sorted(gh.merged),
          "| intents:", len(s["intents"]))
