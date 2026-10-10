"""Debt survives retries, alias changes and removal/reintroduction of law."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixture import World, T0, DAY, make_law


def debt(w, ident="pr42-ci"):
    h = w.journal.health()
    return next(x for x in h["open"] + h["escalated"] if x.get("target") == ident)


class DebtTests(unittest.TestCase):
    def test_eight_attempts_cannot_move_deadline(self):
        w = World()
        initial = debt(w)
        for i in range(8):
            w.add("heartbeat", "sentinel", T0 + i + 1, seen=w.state["size"])
            current = debt(w)
            self.assertEqual((current["opened"], current["due"]), (initial["opened"], initial["due"]))

    def test_renamed_target_with_longer_due_keeps_original_deadline(self):
        w = World()
        initial = debt(w)
        law = copy.deepcopy(w.law)
        law["targets"][0]["id"] = "new-alias"
        law["targets"][0]["due_ms"] = 10 * DAY
        w.widen("law", T0 + 1, release=law)
        current = debt(w, "new-alias")
        self.assertEqual((current["opened"], current["due"]), (initial["opened"], initial["due"]))

    def test_retirement_is_visible_and_reintroduction_keeps_debt(self):
        w = World()
        initial = debt(w)
        removed = copy.deepcopy(w.law)
        removed["targets"] = []
        _, at = w.widen("law", T0 + 1, release=removed)
        history = w.journal.health()["retired"]
        self.assertEqual(history[0]["subject"], "repo:pr:42|ci")
        self.assertEqual(history[0]["status"], "REQUIREMENT_RETIRED_WITHOUT_REPAIR_PROOF")
        returned = copy.deepcopy(w.law)
        returned["targets"][0]["id"] = "returned"
        returned["targets"][0]["due_ms"] = 10 * DAY
        w.widen("law", at, release=returned)
        current = debt(w, "returned")
        self.assertEqual((current["opened"], current["due"]), (initial["opened"], initial["due"]))

    def test_same_alias_retargeted_does_not_erase_old_subject(self):
        w = World()
        law = copy.deepcopy(w.law)
        law["targets"][0]["resource"] = "repo:pr:43"
        w.widen("law", T0 + 1, release=law)
        self.assertEqual(debt(w)["subject"], "repo:pr:43|ci")
        self.assertTrue(any(x["subject"] == "repo:pr:42|ci" for x in w.journal.health()["retired"]))


if __name__ == "__main__":
    unittest.main()
