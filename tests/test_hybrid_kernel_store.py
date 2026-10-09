"""Persistence, replay and rollback-rejection tests for the hybrid admission path."""
import base64,os,sqlite3,tempfile,unittest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding,PublicFormat
from tcb.canon import canon,digest
from tcb.crypto import PAYLOAD_TYPE,keyid,statement,pae
from hybrid_kernel.core import compile_constitution
from hybrid_kernel.store import SQLiteAdmission,StoreError

LAW={"release":"test","max_due_ms":604800000,"rules":[
 {"id":"repair","operation":"repair","requires":{"all":[{"eq":["subject","agent"]}]},
 "opens":[{"kind":"vulnerability","key_field":"resource"}],"closes":[],"effect":False}]}

class StoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=os.path.join(self.tmp.name,"state.db")
        self.private=Ed25519PrivateKey.generate()
        pub=base64.b64encode(self.private.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw)).decode()
        key={"alg":"ed25519","public":pub,"keyid":keyid(pub)}
        self.root={"key":key,"signer":key["keyid"],"domain":"genesis:test"}
        self.law=compile_constitution(LAW)
        self.req=lambda i:{"id":i,"operation":"repair","subject":"agent","resource":"repo:a","changes":[],"effect":False}
    def tearDown(self):self.tmp.cleanup()
    def signed(self,state,req,allowed=True):
        body={"id":"attestation:"+req["id"],"request_digest":digest(req),"state_head":state["head"],
            "law":self.law["pinned"],"subject":req["subject"],"allowed":allowed,
            "now":1000,"observations":[]}
        payload=canon(statement(self.root["domain"],"hybrid-admission",body))
        return {"payloadType":PAYLOAD_TYPE,"payload":base64.b64encode(payload).decode(),
            "signatures":[{"keyid":self.root["signer"],
              "sig":base64.b64encode(self.private.sign(pae(payload))).decode()}]}
    def test_genesis_once_and_reopen(self):
        with SQLiteAdmission(self.path,self.law,self.root) as db:
            db.initialize()
            with self.assertRaises(StoreError):db.initialize()
            state=db.read()
            a=db.admit(self.req("a"),self.signed(state,self.req("a")))
            self.assertEqual(a.verdict,"ACCEPT")
            opened=db.read()["obligations"]
        with SQLiteAdmission(self.path,self.law,self.root) as db:
            self.assertEqual(db.read()["obligations"],opened)
            before=db.read()
            db.admit(self.req("b"),self.signed(before,self.req("b")))
            self.assertEqual(db.read()["obligations"],opened)
            self.assertEqual(db.read()["epoch"],2)
    def test_replay_and_stale_signed_receipt(self):
        with SQLiteAdmission(self.path,self.law,self.root) as db:
            db.initialize()
            first=db.read()
            req=self.req("x")
            receipt=self.signed(first,req)
            db.admit(req,receipt)
            with self.assertRaises(StoreError):db.admit(req,receipt)
            from hybrid_kernel.core import Invalid
            with self.assertRaises(Invalid):db.admit(self.req("y"),self.signed(first,self.req("y")))
            self.assertEqual(db.read()["epoch"],1)
    def test_denial_does_not_advance_ledger(self):
        with SQLiteAdmission(self.path,self.law,self.root) as db:
            db.initialize()
            s=db.read()
            d=db.admit(self.req("x"),self.signed(s,self.req("x"),False))
            self.assertEqual(d.verdict,"REJECT")
            self.assertEqual(db.read()["epoch"],0)
    def test_corrupted_checkpoint_rejected(self):
        with SQLiteAdmission(self.path,self.law,self.root) as db:
            db.initialize()
            s=db.read()
            db.admit(self.req("x"),self.signed(s,self.req("x")))
            db.db.execute("UPDATE checkpoint SET state=? WHERE slot=1",(canon(s),))
            with self.assertRaises(StoreError):db.read()
if __name__=="__main__":unittest.main()
