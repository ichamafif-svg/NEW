"""Only signed constitutional statements can enter the unified boundary."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixture import World, T0, Refused, public, keyid
from tcb.sign import envelope
from hybrid_kernel.trusted import judge_signed


class TrustedAdmission(unittest.TestCase):
    def test_signed_restriction_admitted(self):
        w = World()
        e, _ = w.signed("freeze", "carol", T0 + 1, scope="*")
        self.assertEqual(judge_signed(w.kernel, w.state, e["envelope"]).verdict, "ACCEPT")

    def test_signed_allowed_receipt_is_not_authority(self):
        w = World()
        body = {"id": "receipt", "author": "carol", "at": T0 + 1, "allowed": True}
        env = envelope(w.state["domain"], "hybrid-admission", body, [w.cosigner("carol")])
        self.assertEqual(judge_signed(w.kernel, w.state, env).code, "TYPE.KIND")

    def test_signed_foreign_domain_refused(self):
        w = World()
        body = {"id": "foreign", "author": "carol", "at": T0 + 1, "scope": "*"}
        env = envelope("foreign-domain", "freeze", body, [w.cosigner("carol")])
        self.assertEqual(judge_signed(w.kernel, w.state, env).code, "SIG.DOMAIN")

    def test_unsigned_metadata_refused(self):
        w = World()
        e, _ = w.signed("freeze", "carol", T0 + 1, scope="*")
        e["envelope"]["allowed"] = True
        self.assertEqual(judge_signed(w.kernel, w.state, e["envelope"]).code, "SIG.ENVELOPE")

    def test_one_human_cannot_grant(self):
        w = World()
        e, _ = w.signed("grant", "alice", T0 + 1, holder="agent", actions=["effect:merge"],
                        resources=["repo:*"], conditions=[], not_after=T0 + 100000000)
        self.assertEqual(judge_signed(w.kernel, w.state, e["envelope"]).code, "FLOOR0.QUORUM")

    def test_untrusted_object_cannot_replace_kernel(self):
        w = World()
        with self.assertRaises(Refused):
            judge_signed({"allowed": True}, w.state, {})


if __name__ == "__main__":
    unittest.main()
