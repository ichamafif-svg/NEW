"""The U socket cannot issue effects; real K still judges signed submissions."""
import stat
import errno
import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixture import World, T0
from hybrid_kernel.deployment import GovernedDeployment
from hybrid_kernel.gateway import AdmissionGateway
from standard import GatewayClient, Route, StandardService, WorkEngine
from standard.worker import Worker, run_once
from maintenance.constitution import agent_view


class Boundary:
    def __init__(self):
        self.roles = {f"T{i:02}" for i in range(1, 10)}

    def check(self, *, required, **_):
        if not required <= self.roles:
            raise ValueError("unavailable")


class ProductGatewayTests(unittest.TestCase):
    def test_external_worker_can_submit_but_cannot_close_the_obligation(self):
        world = World()
        try:
            class Client(GatewayClient):
                def __init__(self): self.submissions = []
                def constitutional_view(self):
                    return agent_view(world.kernel, world.state, world.journal.health())
                def qualify_route(self, required): return None
                def admit(self, envelope):
                    self.submissions.append(envelope)
                    return envelope

            client = Client()
            service = StandardService(client, [Route("probe", "RUN", "repo:*",
                                                      frozenset({"observe"}), frozenset({"T06"}))])
            with tempfile.TemporaryDirectory() as tmp:
                engine = WorkEngine(Path(tmp) / "work.sqlite3", service)
                task = next(t for t in service.inspect()["tasks"] if t["state"] == "READY")
                entry, _ = world.signed("observation", "ci", T0 + 1, under="missing",
                                        resource=task["resource"], property="coverage",
                                        status="complete", level="real")
                candidate = entry["envelope"]
                worker = Worker("probe", (sys.executable, "-c",
                    "import json,sys; text=sys.stdin.read(); assert text.startswith('# Standard · contexte'); "
                    "assert 'Loi applicable' in text; print(json.dumps({'envelope':" + repr(candidate) + "}))"), tmp)
                result = run_once(engine, [worker], mode="RUN", now=1)
                self.assertEqual(result["status"], "SUBMITTED")
                self.assertFalse(result["obligation_closed"])
                self.assertEqual(client.submissions, [candidate])
                self.assertTrue(any(t["obligation"] == result["task"].rsplit(":", 1)[0]
                                    for t in service.inspect()["tasks"]))
                engine.close()
        finally:
            world.journal.close()

    def test_client_sees_work_and_can_submit_only_to_constitutional_admission(self):
        world = World()
        boundary = Boundary()
        try:
            with tempfile.TemporaryDirectory() as tmp:
                with GovernedDeployment(ledger_path=world.path, pin_store=world.pins,
                                        genesis_pin=world.state["domain"], trust_boundary=boundary,
                                        trusted_now=lambda: T0 + 1) as deployment:
                    try:
                        gateway = AdmissionGateway(Path(tmp) / "admission.sock", deployment)
                    except OSError as exc:
                        if exc.errno == errno.EPERM:
                            self.skipTest("Unix sockets are disallowed in this sandbox")
                        raise
                    server = threading.Thread(target=gateway.serve_forever, daemon=True)
                    server.start()
                    try:
                        self.assertEqual(stat.S_IMODE(Path(gateway.server_address).stat().st_mode), 0o600)
                        client = GatewayClient(gateway.server_address)
                        self.assertFalse(hasattr(client, "guard"))
                        service = StandardService(client, [
                            Route("scan", "RUN", "repo:*", frozenset({"observe"}), frozenset({"T06"}))])
                        view = service.inspect()
                        self.assertEqual(view["basis"]["head"], world.state["head"])
                        boundary.roles.remove("T06")
                        blocked = service.inspect()
                        self.assertEqual(blocked["qualification_work"][0]["route"], "scan")
                        # A missing evidence instrument does not block an
                        # independently signed immediate restriction.
                        entry, _ = world.signed("freeze", "carol", T0 + 1, scope="*")
                        client.admit(entry["envelope"])
                        self.assertNotEqual(deployment.snapshot()["head"], view["basis"]["head"])
                        self.assertEqual(service.inspect()["routes"][0]["state"], "TRUST_BLOCKED")
                    finally:
                        gateway.shutdown()
                        gateway.server_close()
                        server.join(timeout=5)
        finally:
            world.journal.close()


if __name__ == "__main__": unittest.main()
