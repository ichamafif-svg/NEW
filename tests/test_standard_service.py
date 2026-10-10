"""An integration surface for work, route trust and constitutional admission."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixture import World, Refused, T0, DAY, make_law
from hybrid_kernel.deployment import GovernedDeployment, ProductionBlocked
from maintenance.constitution import agent_view
from standard import Route, StandardService, WorkEngine, WorkError
from standard.service import _law_trust


class Installed:
    def __init__(self, world):
        self.world = world
        self.blocked = set()
        self.forwarded = []

    def constitutional_view(self):
        return agent_view(self.world.kernel, self.world.state, self.world.journal.health())

    def qualify_route(self, roles):
        if self.blocked.intersection(roles):
            raise ProductionBlocked("TRUST.REQUIRED_ROLE_UNAVAILABLE")

    def admit(self, envelope):
        self.forwarded.append(envelope)
        return envelope

    def guard(self, **kwargs):
        return kwargs


class StandardServiceTests(unittest.TestCase):
    def setUp(self):
        self.world = World()
        self.deployment = Installed(self.world)
        self.service = StandardService(self.deployment, [
            Route("scanner", "BOTH", "repo:*", frozenset({"observe", "cover"}), frozenset({"T06"})),
            Route("builder", "BUILD", "repo:*", frozenset({"build"}), frozenset({"T07"})),
        ])

    def tearDown(self):
        self.world.journal.close()

    def test_one_prefix_law_and_stable_work_across_modes(self):
        run = self.service.inspect(mode="RUN")
        build = self.service.inspect(mode="BUILD")
        self.assertEqual(run["basis"], build["basis"])
        self.assertEqual(run["law"], build["law"])
        self.assertTrue(run["read_only"])
        self.assertTrue(any(t["state"] == "HUMAN_REVIEW" for t in run["tasks"]))
        self.assertEqual([t["id"] for t in run["tasks"]],
                         [t["id"] for t in self.service.inspect()["tasks"]])

    def test_trust_loss_blocks_only_the_dependent_route(self):
        self.deployment.blocked.add("T06")
        cycle = self.service.inspect()
        scanner_tasks = [t for t in cycle["tasks"] if any(r["id"] == "scanner" for r in t["routes"])]
        self.assertTrue(scanner_tasks)
        self.assertTrue(all(t["state"] == "TRUST_BLOCKED" for t in scanner_tasks))
        self.assertEqual(cycle["qualification_work"], [{"id": "qualify:scanner", "route": "scanner",
                                                       "required_t": ["T06"],
                                                       "closure": "independent_live_qualification"}])
        self.assertTrue(any(t["state"] == "HUMAN_REVIEW" for t in cycle["tasks"]))

    def test_submission_requires_current_work_and_qualified_route(self):
        cycle = self.service.inspect()
        task = next(t for t in cycle["tasks"] if t["state"] == "READY")
        entry, _ = self.world.signed("observation", "ci", T0 + 1,
                                     under="missing", resource=task["resource"],
                                     property="coverage", status="complete", level="real")
        env = entry["envelope"]
        self.assertEqual(self.service.submit(mode="RUN", task_id=task["id"], route_id="scanner",
                                             basis=cycle["basis"], envelope=env), env)
        self.assertEqual(self.deployment.forwarded, [env])
        self.deployment.blocked.add("T06")
        with self.assertRaises(WorkError):
            self.service.submit(mode="RUN", task_id=task["id"], route_id="scanner",
                                basis=cycle["basis"], envelope=env)
        self.assertEqual(self.deployment.forwarded, [env])
        self.deployment.blocked.clear()
        stale = dict(cycle["basis"], head="stale")
        with self.assertRaises(WorkError):
            self.service.submit(mode="RUN", task_id=task["id"], route_id="scanner",
                                basis=stale, envelope=env)

    def test_route_declaration_is_not_a_grant(self):
        with self.assertRaises(WorkError):
            Route("bad", "RUN", "repo:*", frozenset({"observe"}), frozenset({"T99"}))
        with self.assertRaises(WorkError):
            StandardService(self.deployment, [Route("a", "RUN", "*", frozenset({"observe"}))] * 2)
        self.assertNotIn("allowed", self.service.inspect())

    def test_build_route_inherits_effect_trust_from_pinned_law(self):
        cycle = self.service.inspect(mode="BUILD")
        law = cycle["law"]
        self.assertTrue({"T07", "T08"} <= _law_trust(law, "repo:deps:vulns", "build"))
        self.assertIn("T06", _law_trust(law, "repo:deps:vulns", "observe"))

    def test_client_can_only_add_trust_to_floor_operation(self):
        world = World(law=make_law(tighten={"ops": {"remediate": {"trusted": ["T09"]}}}))
        try:
            effective = world.kernel.law_of(world.state).release
            self.assertEqual(_law_trust(effective, "repo:deps:vulns", "build"), {"T07", "T08", "T09"})
        finally:
            world.journal.close()

    def test_task_cannot_be_satisfied_by_a_signed_unrelated_statement(self):
        cycle = self.service.inspect()
        task = next(t for t in cycle["tasks"] if t["state"] == "READY")
        entry, _ = self.world.signed("observation", "ci", T0 + 1, under="missing",
                                     resource="repo:other:subject", property="coverage",
                                     status="complete", level="real")
        with self.assertRaises(WorkError):
            self.service.submit(mode="RUN", task_id=task["id"], route_id="scanner",
                                basis=cycle["basis"], envelope=entry["envelope"])
        self.assertEqual(self.deployment.forwarded, [])

    def test_durable_retry_does_not_close_or_postpone_constitutional_debt(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "work.sqlite3"
            engine = WorkEngine(path, self.service)
            cycle = engine.sync()
            first = engine.claim(now=1)
            self.assertIsNotNone(first)
            self.assertEqual(first["due"], next(t["due"] for t in cycle["tasks"] if t["id"] == first["id"]))
            engine.complete_attempt(mode="RUN", task_id=first["id"], lease_until=first["lease_until"], next_at=100_000)
            with self.assertRaises(WorkError):
                engine.complete_attempt(mode="RUN", task_id=first["id"], lease_until=first["lease_until"], next_at=0)
            engine.close()
            engine = WorkEngine(path, self.service)
            engine.sync()
            stored = engine.db.execute("SELECT due,attempts,next_at FROM tasks WHERE mode=? AND id=?",
                                       ("RUN", first["id"])).fetchone()
            self.assertEqual(stored, (first["due"], 1, 100_000))
            self.assertTrue(any(t["obligation"] == first["id"].rsplit(":", 1)[0]
                                for t in self.service.inspect()["tasks"]))
            engine.close()

    def test_real_kt_admission_refuses_agent_route_as_grant_authority(self):
        class Boundary:
            def check(self, **kwargs):
                self.required = kwargs["required"]

        with GovernedDeployment(ledger_path=self.world.path, pin_store=self.world.pins,
                                genesis_pin=self.world.state["domain"], trust_boundary=Boundary(),
                                trusted_now=lambda: T0 + 1) as installed:
            service = StandardService(installed, [
                Route("scanner", "RUN", "repo:*", frozenset({"observe"}), frozenset({"T06"}))])
            cycle = service.inspect()
            task = next(t for t in cycle["tasks"] if t["state"] == "READY")
            entry, _ = self.world.signed("observation", "ci", T0 + 1,
                                         under="missing", resource=task["resource"],
                                         property="coverage", status="complete", level="real")
            with self.assertRaises(Refused):
                service.submit(mode="RUN", task_id=task["id"], route_id="scanner",
                               basis=cycle["basis"], envelope=entry["envelope"])
            self.assertEqual(installed.snapshot()["head"], cycle["basis"]["head"])


if __name__ == "__main__":
    unittest.main()
