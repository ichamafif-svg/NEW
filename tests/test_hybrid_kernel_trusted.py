"""Integration tests for authenticated DSSE admission boundary."""
import base64
import unittest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding,PublicFormat
from tcb.canon import canon,digest
from tcb.crypto import statement,pae,PAYLOAD_TYPE,keyid
from hybrid_kernel.core import compile_constitution,genesis,Invalid
from hybrid_kernel.trusted import judge_signed

LAW={"release":"test","max_due_ms":86400000,"rules":[{
"id":"repair","operation":"repair","requires":{"all":[{"eq":["subject","agent"]}]},
"opens":[{"kind":"vulnerability","key_field":"resource"}],"closes":[],"effect":False}]}

class TrustedAdmission(unittest.TestCase):
    def setUp(self):
        self.private=Ed25519PrivateKey.generate()
        pub=base64.b64encode(self.private.public_key().public_bytes(
            Encoding.Raw,PublicFormat.Raw)).decode()
        key={"alg":"ed25519","public":pub,"keyid":keyid(pub)}
        self.root={"key":key,"signer":key["keyid"],"domain":"test-genesis"}
        self.law=compile_constitution(LAW)
        self.state=genesis(self.law)
        self.request={"id":"i1","operation":"repair","subject":"agent",
                      "resource":"repo:a","changes":[],"effect":False}
    def receipt(self,request=None,head=None,allowed=True):
        r=request or self.request
        body={"id":"receipt-1","request_digest":digest(r),"state_head":head or self.state["head"],
              "law":self.law["pinned"],"subject":r["subject"],"allowed":allowed,
              "now":1000,"observations":[]}
        payload=canon(statement(self.root["domain"],"hybrid-admission",body))
        sig=self.private.sign(pae(payload))
        return {"payloadType":PAYLOAD_TYPE,"payload":base64.b64encode(payload).decode(),
                "signatures":[{"keyid":self.root["signer"],"sig":base64.b64encode(sig).decode()}]}
    def test_admit_signed(self):
        self.assertEqual(judge_signed(self.state,self.law,self.request,
                                     self.receipt(),self.root).verdict,"ACCEPT")
    def test_foreign_request_rejected(self):
        changed={**self.request,"resource":"repo:b"}
        with self.assertRaises(Invalid):
            judge_signed(self.state,self.law,changed,self.receipt(),self.root)
    def test_unauthorized_signed_deny(self):
        self.assertEqual(judge_signed(self.state,self.law,self.request,
                                     self.receipt(allowed=False),self.root).verdict,"REJECT")
    def test_foreign_signer_rejected(self):
        other=Ed25519PrivateKey.generate()
        envelope=self.receipt()
        envelope["signatures"][0]["sig"]=base64.b64encode(
            other.sign(pae(base64.b64decode(envelope["payload"])))).decode()
        with self.assertRaises(Invalid):
            judge_signed(self.state,self.law,self.request,envelope,self.root)
    def test_cross_state_replay_rejected(self):
        envelope=self.receipt()
        state={**self.state,"head":"sha256:"+"f"*64}
        with self.assertRaises(Invalid):judge_signed(state,self.law,self.request,envelope,self.root)
if __name__=="__main__":unittest.main()
