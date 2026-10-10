"""One judgment: relational constraints, finite transitions, exhaustive deltas."""
import copy
import sys
import unittest
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixture import World, T0, DAY, Refused, make_law, digest
from hybrid_kernel.core import Kernel, empty
from hybrid_kernel.model import detached, Relation
from tcb import Kernel as CompatibilityKernel
from tcb.invariants import Invariants, Disagreement

RESOURCE = {
    "fields": {"revision": "int", "label": "str"},
    "states": ["open", "ready"], "initial": "open",
    "transitions": {"prepare": {"from": ["open"], "to": "ready", "writes": ["revision"],
        "requires": {"all": [{"related": ["owns", "$author", "$resource"]},
                                {"related": ["state", "$resource", "open"]}]}}},
}


def world():
    return World(law=make_law(resources={"artifact": copy.deepcopy(RESOURCE)}))


def registered(w):
    gid, at = w.grant("agent", ["register:artifact", "transition:artifact:prepare"], ["asset:*"], T0 + 1)
    w.add("resource", "agent", at, under=gid, resource="asset:a", type="artifact", fields={"revision": 0, "label": "A"})
    return gid, at + 1


class CoreTests(unittest.TestCase):
    def test_compatibility_is_the_same_class(self):
        self.assertIs(Kernel, CompatibilityKernel)
        self.assertEqual(Kernel.__module__, "hybrid_kernel.core")

    def test_stable_relational_model(self):
        w = world()
        gid, at = registered(w)
        graph = w.kernel.graph(w.state)
        self.assertIn(Relation("owns", "agent", "asset:a"), graph)
        self.assertIn(Relation("state", "asset:a", "open"), graph)
        self.assertIn(Relation("holds", "agent", gid), graph)
        self.assertEqual(graph, tuple(sorted(graph)))

    def test_exhaustive_transition_and_pure_judgment(self):
        w = world()
        gid, at = registered(w)
        state = detached(w.state)
        candidate, _ = w.signed("transition", "agent", at, under=gid, resource="asset:a", operation="prepare",
                                 expected=digest(state["entities"]["asset:a"]), changes={"revision": 1})
        original = copy.deepcopy(state)
        d = w.kernel.judgment(state, candidate)
        self.assertEqual(state, original)
        self.assertEqual(d.verdict, "ACCEPT")
        result = w.kernel.commit(state, d)
        self.assertEqual(result["entities"]["asset:a"]["state"], "ready")
        self.assertEqual(result["entities"]["asset:a"]["version"], 2)
        self.assertEqual(result["entities"]["asset:a"]["fields"], {"revision": 1, "label": "A"})
        w.journal.append(candidate)
        self.assertEqual(detached(w.state), detached(result))

    def test_missing_or_additional_delta_writes_refused(self):
        for changes in ({}, {"revision": 1, "label": "B"}, {"revision": 1, "owner": "agent"}):
            w = world()
            gid, at = registered(w)
            w.refuse("DELTA.EXHAUSTIVE", "transition", "agent", at, under=gid, resource="asset:a",
                     operation="prepare", expected=digest(detached(w.state["entities"]["asset:a"])), changes=changes)

    def test_wrong_scalar_type_refused(self):
        w = world()
        gid, at = registered(w)
        w.refuse("TYPE.FIELDS", "transition", "agent", at, under=gid, resource="asset:a", operation="prepare",
                 expected=digest(detached(w.state["entities"]["asset:a"])), changes={"revision": True})

    def test_stale_resource_and_duplicate_registration(self):
        w = world()
        gid, at = registered(w)
        w.refuse("STATE.CONFLICT", "transition", "agent", at, under=gid, resource="asset:a", operation="prepare",
                 expected=digest({"fake": "prefix"}), changes={"revision": 1})
        w.refuse("STATE.EXISTS", "resource", "agent", at, under=gid, resource="asset:a", type="artifact",
                 fields={"revision": 0, "label": "alias"})

    def test_freeze_immediately_blocks_transition(self):
        w = world()
        gid, at = registered(w)
        w.add("freeze", "sentinel", at, scope="asset:*")
        w.refuse("FREEZE.ACTIVE", "transition", "agent", at + 1, under=gid, resource="asset:a", operation="prepare",
                 expected=digest(detached(w.state["entities"]["asset:a"])), changes={"revision": 1})

    def test_revocation_blocks_even_valid_relational_constraints(self):
        w = world()
        gid, at = registered(w)
        w.add("revoke", "carol", at, grant=gid)
        w.refuse("CAP.WITHDRAWN", "transition", "agent", at + 1, under=gid, resource="asset:a", operation="prepare",
                 expected=digest(detached(w.state["entities"]["asset:a"])), changes={"revision": 1})

    def test_forged_decision_and_stale_commit_refused(self):
        from tcb.canon import canon
        w = world()
        gid, at = registered(w)
        state = detached(w.state)
        candidate, _ = w.signed("transition", "agent", at, under=gid, resource="asset:a", operation="prepare",
                                 expected=digest(state["entities"]["asset:a"]), changes={"revision": 1})
        d = w.kernel.judgment(state, candidate)
        forged = replace(d, delta_bytes=canon(d.delta[:-1]))
        with self.assertRaises(Refused):
            w.kernel.commit(state, forged)
        after = w.kernel.commit(state, d)
        with self.assertRaises(Refused):
            w.kernel.commit(after, d)
        mutated = d.delta
        next(row for row in mutated if row[:2] == ["put", "entities"])[-1]["owner"] = "carol"
        self.assertEqual(w.kernel.commit(state, d)["entities"]["asset:a"]["owner"], "agent")

    def test_second_check_rejects_incomplete_or_forged_consequence(self):
        w = world()
        gid, at = registered(w)
        candidate, _ = w.signed("transition", "agent", at, under=gid, resource="asset:a", operation="prepare",
                                 expected=digest(detached(w.state["entities"]["asset:a"])), changes={"revision": 1})
        record, delta = w.kernel.decide(w.state, candidate)
        checker = Invariants()
        checker.check(w.state, record, delta, candidate, w.kernel.law_of(w.state))
        native = next(row for row in delta if row[:2] == ("put", "entities"))
        forged = [(*row[:3], {**row[3], "owner": "carol"}) if row is native else row for row in delta]
        for corrupted in ([row for row in delta if row is not native], forged, delta[1:]):
            with self.assertRaises(Disagreement):
                checker.check(w.state, record, corrupted, candidate, w.kernel.law_of(w.state))

    def test_unsealed_resource_type_is_refused(self):
        w = World()
        gid, at = w.grant("agent", ["register:artifact"], ["asset:*"], T0 + 1)
        w.refuse("TYPE.RESOURCE", "resource", "agent", at, under=gid, resource="asset:a", type="artifact",
                 fields={"revision": 0, "label": "A"})

    def test_restrictions_share_last_time_even_with_unfulfilled_law(self):
        w = world()
        gid, at = registered(w)
        w.add("freeze", "sentinel", at, scope="asset:*")
        w.add("revoke", "carol", at, grant=gid)
        self.assertIn(gid, w.state["revoked"])

    def test_native_transitions_obey_all_capability_budgets(self):
        w = world()
        gid, at = w.grant("agent", ["register:artifact", "transition:artifact:prepare"], ["asset:*"], T0 + 1,
                           budget={"count": 1, "window": DAY})
        w.add("resource", "agent", at, under=gid, resource="asset:a", type="artifact", fields={"revision": 0, "label": "A"})
        w.refuse("OBL.BUDGET", "transition", "agent", at + 1, under=gid, resource="asset:a", operation="prepare",
                 expected=digest(detached(w.state["entities"]["asset:a"])), changes={"revision": 1})

    def test_law_pin_cannot_be_replaced(self):
        w = World()
        state = detached(w.state)
        state["law"]["digest"] = digest("foreign-law")
        candidate, _ = w.signed("freeze", "carol", T0 + 1, scope="*")
        self.assertEqual(w.kernel.judgment(state, candidate).code, "LAW.PIN")

    def test_identical_input_produces_identical_complete_judgment(self):
        w = world()
        gid, at = registered(w)
        candidate, _ = w.signed("transition", "agent", at, under=gid, resource="asset:a", operation="prepare",
                                 expected=digest(detached(w.state["entities"]["asset:a"])), changes={"revision": 1})
        self.assertEqual(w.kernel.judgment(w.state, candidate), w.kernel.judgment(w.state, candidate))
        record, delta = w.kernel.decide(w.state, candidate)
        self.assertEqual(detached(delta), w.kernel.judgment(w.state, candidate).delta)


if __name__ == "__main__":
    unittest.main()
