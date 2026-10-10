"""Qualified proof binds subject, method, coverage, freshness and independence."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixture import World, T0, DAY, make_law, digest, Refused
from hybrid_kernel.model import detached
from tcb.invariants import Invariants, Disagreement

INSTRUMENT = {"method": "ci-v1", "coverage": "repo:inventory:all", "sources": ["ci"], "min_level": "real", "fresh_ms": 10000}


def world():
    return World(law=make_law(instruments={"ci": copy.deepcopy(INSTRUMENT)}))


def ready(w):
    gid, at = w.grant("ci", ["observe", "certify:real"], ["repo:*"], T0 + 1)
    return gid, at


def fields(gid, at):
    return {"under": gid, "resource": "repo:pr:42", "property": "ci", "status": "green", "level": "real",
            "method": "ci-v1", "coverage": "repo:inventory:all", "measured_at": at, "artifact": digest("result")}


class MeasurementTests(unittest.TestCase):
    def test_measurement_can_prove_target_after_coverage(self):
        w = world()
        gid, at = ready(w)
        w.add("observation", "ci", at, under=gid, resource="repo:inventory:all", property="coverage", status="complete", level="real")
        ident = w.add("measurement", "ci", at + 1, **fields(gid, at + 1))
        h = w.journal.health()
        self.assertIn({"target": "pr42-ci", "evidence": ident}, h["proven"])

    def test_plain_observation_cannot_bypass_required_instrument(self):
        w = world()
        gid, at = ready(w)
        w.refuse("PROV.INSTRUMENT", "observation", "ci", at, under=gid, resource="repo:pr:42", property="ci", status="green", level="real")

    def test_wrong_method_coverage_or_source_refused(self):
        for override in ({"method": "wrong"}, {"coverage": "repo:other"}):
            w = world()
            gid, at = ready(w)
            w.refuse("PROV.COVERAGE", "measurement", "ci", at, **{**fields(gid, at), **override})
        w = world()
        gid, at = w.grant("readback", ["observe", "certify:real"], ["repo:*"], T0 + 1)
        w.refuse("PROV.COVERAGE", "measurement", "readback", at, **fields(gid, at))

    def test_stale_or_future_measurement_refused(self):
        for offset in (-10001, 1):
            w = world()
            gid, at = ready(w)
            w.refuse("PROV.STALE", "measurement", "ci", at, **{**fields(gid, at), "measured_at": at + offset})

    def test_invalidation_immediately_removes_proof(self):
        w = world()
        gid, at = ready(w)
        w.add("observation", "ci", at, under=gid, resource="repo:inventory:all", property="coverage", status="complete", level="real")
        ident = w.add("measurement", "ci", at + 1, **fields(gid, at + 1))
        w.add("invalidate", "carol", at + 1, evidence=ident)
        h = w.journal.health()
        self.assertNotIn("pr42-ci", {x["target"] for x in h["proven"]})
        self.assertTrue(any(x.get("target") == "pr42-ci" for x in h["open"] + h["escalated"]))

    def test_instrument_cannot_invalidate_another_instrument(self):
        w = world()
        gid, at = ready(w)
        ident = w.add("measurement", "ci", at, **fields(gid, at))
        w.refuse("CAP.RESTRICT", "invalidate", "readback", at, evidence=ident)
        w.add("invalidate", "ci", at, evidence=ident)

    def test_expiry_exposes_debt_at_exact_measurement_expiry(self):
        w = world()
        gid, at = ready(w)
        w.add("observation", "ci", at, under=gid, resource="repo:inventory:all", property="coverage", status="complete", level="real")
        w.add("measurement", "ci", at + 1, **fields(gid, at + 1))
        h = w.journal.health(required_at=at + 10002)
        self.assertNotIn("pr42-ci", {x["target"] for x in h["proven"]})
        ob = next(x for x in h["open"] + h["escalated"] if x.get("target") == "pr42-ci")
        self.assertEqual(ob["opened"], at + 10002)

    def test_invalidated_measurement_cannot_permit_an_effect(self):
        w = World(law=make_law(instruments={"ci": copy.deepcopy(INSTRUMENT)},
                              conditions={"healthy": {"all": [{"observed": ["ci", "green", "real"]}]}}))
        ci, at = ready(w)
        agent, at = w.grant("agent", ["effect:merge"], ["repo:pr:*"], at, conditions=["healthy"])
        ident = w.add("measurement", "ci", at, **fields(ci, at))
        w.add("intent", "agent", at + 1, under=agent, op="merge", args={"pr": "42", "method": "squash"})
        w.add("invalidate", "carol", at + 2, evidence=ident)
        w.refuse("LAW.CONDITION", "intent", "agent", at + 3, under=agent, op="merge", args={"pr": "42", "method": "squash"})

    def test_second_check_rejects_forged_measurement(self):
        w = world()
        gid, at = ready(w)
        e, _ = w.signed("measurement", "ci", at, **fields(gid, at))
        record, delta = w.kernel.decide(w.state, e)
        next(row for row in delta if row[:2] == ("put", "observations"))[3]["coverage"] = "repo:foreign"
        with self.assertRaises(Disagreement):
            Invariants().check(w.state, record, delta, e, w.kernel.law_of(w.state))

    def test_no_coverage_does_not_close_target(self):
        w = world()
        gid, at = ready(w)
        w.add("measurement", "ci", at, **fields(gid, at))
        self.assertNotIn("pr42-ci", {x["target"] for x in w.journal.health()["proven"]})


if __name__ == "__main__":
    unittest.main()
