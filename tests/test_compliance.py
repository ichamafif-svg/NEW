"""The compliance dossier is a projection of the replayed journal: rebuilt byte for byte, never trusted as written."""
import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixture import T0, World, run  # noqa: E402
from test_accountability import ci, observe  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from compliance.dossier import CATALOG, GAP, PARTIAL, PROVEN, build, render, rows_of, verify  # noqa: E402


def world():
    w = World()
    gid, t = ci(w, T0 + 1)
    observe(w, gid, t, "repo:inventory:all", "coverage", "complete")
    observe(w, gid, t + 1, "repo:deps:vulns", "high", "none")
    officer, t = w.grant("carol", ["observe", "certify:real"], ["org:*"], t + 2)
    observe(w, officer, t, "org:controls:soa", "coverage", "complete", author="carol")
    observe(w, officer, t + 1, "org:incident:procedure", "attested", "current", author="carol")
    s = w.state
    return w, rows_of(w.path), [{"size": s["size"], "head": s["head"]}], s["domain"], t + 2


def test_catalog_covers_the_three_frameworks():
    sizes = {f["id"]: len(f["controls"]) for f in CATALOG["frameworks"]}
    assert sizes == {"iso27001": 93, "nis2": 12, "dora": 19}, sizes


def test_statuses_follow_signed_evidence():
    w, rows, pins, genesis, at = world()
    d = build(rows, genesis_pin=genesis, checkpoints=pins, required_at=at)
    m = d["measures"]
    assert m["vulns"]["status"] == PROVEN and m["vulns"]["evidence"]["author"] == "ci"
    assert m["incident"]["status"] == PROVEN and m["incident"]["evidence"]["author"] == "carol"
    assert m["journal"]["status"] == PROVEN and m["secrets"]["status"] == GAP and d["applicability"] == PROVEN
    iso = {c["id"]: c["status"] for c in d["frameworks"][0]["controls"]}
    assert iso["5.24"] == PROVEN and iso["5.21"] == PARTIAL and iso["7.1"] == GAP
    nis2 = {c["id"]: c["status"] for c in d["frameworks"][1]["controls"]}
    assert nis2["Art. 23"] == PROVEN
    assert "Dossier de conformité" in render(d)


def test_a_dossier_is_genuine_only_if_the_journal_rebuilds_it():
    w, rows, pins, genesis, at = world()
    d = build(rows, genesis_pin=genesis, checkpoints=pins, required_at=at)
    assert verify(d, rows, checkpoints=pins)
    forged = copy.deepcopy(d)
    forged["measures"]["secrets"]["status"] = PROVEN
    assert not verify(forged, rows, checkpoints=pins)
    later = build(rows, genesis_pin=genesis, checkpoints=pins, required_at=at + 400 * 86_400_000)
    assert later["measures"]["incident"]["status"] == GAP                   # an attestation expires on its own


if __name__ == "__main__":
    run(globals())
