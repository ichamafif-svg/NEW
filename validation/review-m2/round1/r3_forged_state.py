"""R3: the state branches are the only source of genesis.json, journal and pins. Whoever can push to
standard-journal / standard-pins (every job's GITHUB_TOKEN: workflow-level contents: write + persisted checkout
credentials; the agent App token, which must have contents: write to push branches) replaces them with a ledger
it minted itself. The guard job, holding the real guard key and the bypass App, then merges whatever that ledger
says; `compliance verify` accepts the forged dossier because it takes the genesis pin from the dossier itself."""
import json
import os
from pathlib import Path

from harness import World, make_keys, GOOD
from tcb.floors import FLOORS


class GH:
    def __init__(self):
        self.merged = set()

    def pulls(self):
        return []

    def pull(self, n):
        return {"merged": str(n) in self.merged, "head": {"sha": "f" * 40}}

    def merge(self, n):
        self.merged.add(str(n))


gh = GH()
real = World(gh)                                   # the legitimate deployment (we only need its guard key)
attacker_keys, attacker_publics = make_keys(real.tmp, "mallory")
pubs = json.loads(Path(attacker_publics).read_text())
pubs["guard"] = json.loads(Path(real.publics).read_text())["guard"]      # public, read from the real root
Path(attacker_publics).write_text(json.dumps(pubs))

with real.env():
    real.boot()                                    # the humans' genesis; its pin is the admin variable
REAL_PIN = real.pin
forged = World(gh, measured=GOOD)
forged.keys, forged.publics = attacker_keys, attacker_publics
with forged.env():
    forged.boot()                                  # attacker-made genesis, root, grants, witnesses
    forged.clock.t += 60
    s = forged.step("scan")
    from ops.node import Node
    from ops.cycle import grant_of
    n = Node(forged.state, attacker_keys, expected_genesis=forged.pin)
    try:
        under = grant_of(n.state, "scanner", action="observe")
        res = "repo:code:sast/pr/666/" + "f" * 40       # an arbitrary code PR, never reviewed by anyone
        for prop, st in (("ci", "green"), ("scope", "dependencies")):
            n.add("observation", "scanner", under=under, resource=res, property=prop, status=st, level="real")
        n.retain()
    finally:
        n.close()
    for t in FLOORS["targets"]:                    # and every organisational attestation, "signed by" the officer
        if t["resource"].startswith("org:"):
            forged.step("attest", resource=t["resource"])
    forged.step("ask")
    real_guard_only = {"guard": real.keys["guard"]}        # what the guard job holds (secrets.GUARD_KEYS)
    forged_pin, forged.pin = forged.pin, REAL_PIN       # the guard job reads STANDARD_GENESIS, not the branch
    try:
        s = forged.step("guard", keys=real_guard_only)
        print("guard executed on forged ledger:", list(s["executed"].values()))
    except ValueError as exc:
        print("guard on forged ledger refused:", exc)
    print("PUT:", [c[1] for c in forged.calls if c[0] == "PUT"])
    forged.pin = forged_pin

    from compliance.dossier import build, rows_of, verify
    n = Node(forged.state, attacker_keys, expected_genesis=forged.pin)
    try:
        rows, pins = rows_of(n.journal.path), n.pins.load()
        d = build(rows, genesis_pin=n.genesis, checkpoints=pins, required_at=int(forged.clock.t * 1000))
    finally:
        n.close()
    print("forged dossier counts:", {f["id"]: f["counts"] for f in d["frameworks"]}, "applicability:", d["applicability"])
    print("verify under the trusted (real) genesis:", verify(d, rows, genesis_pin=REAL_PIN, checkpoints=pins))
    print("verify under the dossier's own genesis:", verify(d, rows, genesis_pin=d["genesis"], checkpoints=pins))
