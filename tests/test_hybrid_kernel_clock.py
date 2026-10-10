"""T03 time quotes: fresh challenge, quorum, exact agreement, monotonicity."""
import base64
import unittest

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from hybrid_kernel.clock import WitnessClock, ClockError, PREFIX
from tcb.canon import canon, digest


class ClockTests(unittest.TestCase):
    def setUp(self):
        self.private = {name: Ed25519PrivateKey.from_private_bytes(bytes([n]) * 32)
                        for n, name in enumerate(("a", "b", "c"), 1)}
        self.keys = {name: key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
                     for name, key in self.private.items()}
        self.now = 120
        self.genesis = digest("genesis")

    def quote(self, name, nonce, at=None, genesis=None):
        claim = {"genesis": genesis or self.genesis, "witness": name,
                 "nonce": nonce, "at": self.now if at is None else at}
        return {"claim": claim, "signature": base64.b64encode(
            self.private[name].sign(PREFIX + canon(claim))).decode()}

    def clock(self, fetch):
        return WitnessClock(genesis=self.genesis, public_keys=self.keys,
                            quorum=2, max_skew_ms=0, fetch=fetch)

    def test_fresh_quorum_and_rollback(self):
        clock = self.clock(lambda nonce: [self.quote("a", nonce), self.quote("b", nonce)])
        self.assertEqual(clock(), 120)
        self.now = 121
        self.assertEqual(clock(), 121)
        self.now = 120
        with self.assertRaises(ClockError): clock()

    def test_replayed_quote_cannot_answer_new_nonce(self):
        replay = []

        def fetch(nonce):
            if not replay: replay.extend([self.quote("a", nonce), self.quote("b", nonce)])
            return replay

        clock = self.clock(fetch)
        self.assertEqual(clock(), 120)
        with self.assertRaises(ClockError): clock()

    def test_one_witness_and_disagreement_fail(self):
        with self.assertRaises(ClockError):
            self.clock(lambda nonce: [self.quote("a", nonce)])()
        with self.assertRaises(ClockError):
            self.clock(lambda nonce: [self.quote("a", nonce), self.quote("b", nonce, at=121)])()

    def test_duplicate_witness_and_foreign_genesis_fail(self):
        with self.assertRaises(ClockError):
            self.clock(lambda nonce: [self.quote("a", nonce), self.quote("a", nonce)])()
        with self.assertRaises(ClockError):
            self.clock(lambda nonce: [self.quote("a", nonce),
                                      self.quote("b", nonce, genesis=digest("foreign"))])()

    def test_nonzero_uncertainty_requires_new_kernel_semantics(self):
        with self.assertRaises(ClockError):
            WitnessClock(genesis=self.genesis, public_keys=self.keys, quorum=2,
                         max_skew_ms=1, fetch=lambda _: [])


if __name__ == "__main__": unittest.main()
