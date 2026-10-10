"""Trust is required where an operation uses it, without blocking restrictions."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixture import World, T0, make_law
from tcb.sign import envelope
from tcb.effects import EffectPort
from tcb.canon import canon
from hybrid_kernel.deployment import BASE, TIMED, EFFECT, LawBoundPort, GovernedDeployment, ProductionBlocked


class Boundary:
    def __init__(self, roles):
        self.roles, self.requests = set(roles), []

    def check(self, *, required, **binding):
        self.requests.append((required, binding))
        if not required <= self.roles:
            raise ValueError("missing roles")


class Routes(unittest.TestCase):
    def setUp(self):
        self.world = World()
        self.boundary = Boundary(TIMED)
        self.now = [T0]
        self.effect = EffectPort({"merge": lambda *_: "ok"})
        with patch("hybrid_kernel.deployment.ConstitutionalRuntime") as runtime:
            self.runtime = runtime.return_value
            self.deployed = GovernedDeployment(
                ledger_path="/tmp/ledger", pin_store=object(),
                genesis_pin=self.world.state["domain"], trust_boundary=self.boundary,
                trusted_now=lambda: self.now[0] if self.now[0] is not None else 1 // 0,
                effect_port=self.effect)

    def signed(self, kind):
        return envelope(self.world.state["domain"], kind,
                        {"id": "route", "author": "carol", "at": T0 + 1},
                        [self.world.cosigner("carol")])

    def test_missing_delivery_does_not_block_autonomous_admission(self):
        self.deployed.admit(self.signed("intent"))
        self.assertEqual(self.boundary.requests[-1][0], TIMED)
        self.deployed.health()
        with self.assertRaises(ProductionBlocked): self.deployed.deliver_due()
        self.runtime.admit.assert_called_once()

    def test_measurement_needs_instrument_but_unrelated_work_does_not(self):
        self.deployed.admit(self.signed("intent"))
        with self.assertRaises(ProductionBlocked): self.deployed.admit(self.signed("measurement"))
        with self.assertRaises(ProductionBlocked): self.deployed.admit(self.signed("client-evidence"))
        self.boundary.roles.add("T06")
        self.deployed.admit(self.signed("measurement"))
        self.assertIn("T06", self.boundary.requests[-1][0])

    def test_signed_effect_records_require_effect_roles(self):
        for kind in ("token", "reservation", "execution"):
            with self.subTest(kind=kind), self.assertRaises(ProductionBlocked):
                self.deployed.admit(self.signed(kind))
        self.boundary.roles.update({"T07", "T08"})
        self.deployed.admit(self.signed("execution"))

    def test_guard_needs_effect_and_readback_ports(self):
        with self.assertRaises(ProductionBlocked):
            self.deployed.guard(identity="guard", signer=object())
        self.boundary.roles.update({"T07", "T08"})
        self.deployed.guard(identity="guard", signer=object())
        self.assertIs(self.runtime.guard.call_args.kwargs["effect_port"].port, self.effect)
        self.boundary.roles.remove("T08")
        callback = self.runtime.guard.call_args.kwargs["validity_check"]
        with self.assertRaises(ProductionBlocked): callback()

    def test_effect_port_fixed_by_installation(self):
        self.boundary.roles.update({"T07", "T08"})
        with self.assertRaises(TypeError):
            self.deployed.guard(identity="guard", signer=object(), operation_handlers={"merge": lambda *_: "ok"})
        self.deployed._effect = None
        with self.assertRaisesRegex(ProductionBlocked, "EFFECT_PORT_MISSING"):
            self.deployed.guard(identity="guard", signer=object())

    def test_clock_outage_blocks_effect_but_not_signed_freeze(self):
        self.now[0] = None
        self.deployed.admit(self.signed("freeze"))
        self.assertEqual(self.boundary.requests[-1][0], BASE)
        with self.assertRaises(ProductionBlocked): self.deployed.admit(self.signed("intent"))
        with self.assertRaises(ProductionBlocked):
            self.deployed.guard(identity="guard", signer=object())

    def test_clock_outage_at_start_still_allows_restriction(self):
        with patch("hybrid_kernel.deployment.ConstitutionalRuntime") as runtime:
            deployed = GovernedDeployment(
                ledger_path="/tmp/ledger", pin_store=object(),
                genesis_pin=self.world.state["domain"], trust_boundary=self.boundary,
                trusted_now=lambda: 1 // 0)
        deployed.admit(self.signed("freeze"))
        runtime.return_value.admit.assert_called_once()
        with self.assertRaises(ProductionBlocked): deployed.admit(self.signed("intent"))

    def test_law_specific_trust_blocks_before_provider_departure(self):
        law = make_law(ops={"special": {"args": {"item": "segment"},
                                      "resource": "repo:special:{item}", "profile": "capability",
                                      "trusted": ["T09"]}})
        world = World(law=law)
        sent = []
        port = EffectPort({"special": lambda *args: sent.append(args) or "ok"})
        boundary = Boundary(TIMED | {"T07", "T08"})
        try:
            with GovernedDeployment(ledger_path=world.path, pin_store=world.pins,
                                    genesis_pin=world.state["domain"], trust_boundary=boundary,
                                    trusted_now=lambda: T0 + 1, effect_port=port) as installed:
                judged = {"op": "special", "resource": "repo:special:x", "args": {"item": "x"}}
                from tcb.effects import NotDispatched
                with self.assertRaises(NotDispatched):
                    LawBoundPort(port, installed).perform(judged, canon(judged), "reservation")
                self.assertEqual(sent, [])
        finally:
            world.journal.close()


if __name__ == "__main__": unittest.main()
