"""Hybrid prototype structural and adversarial tests (no claim of physical safety)."""
import unittest
from hybrid_kernel.core import compile_constitution,genesis,judge,commit,Invalid

LAW={"release":"v1","max_due_ms":604800000,"rules":[
    {"id":"repair","operation":"repair","requires":{"all":[{"eq":["subject","agent"]}]},
     "opens":[{"kind":"vulnerability","key_field":"resource"}],"closes":[],"effect":False},
    {"id":"deploy","operation":"deploy","requires":{"all":[{"eq":["subject","agent"]}]},
     "opens":[],"closes":[],"effect":True},
    {"id":"resolve","operation":"resolve","requires":{"all":[{"eq":["subject","agent"]}]},
     "opens":[],"closes":[{"kind":"vulnerability","key_field":"resource"}],"effect":False}]}
def req(ident="i1",op="repair",changes=None,effect=False):
    return {"id":ident,"operation":op,"subject":"agent","resource":"repo:a",
            "changes":[] if changes is None else changes,"effect":effect}
def ctx(t=1000,allowed=True):
    return {"receipt":"verified:fixture-only","subject":"agent",
            "allowed":allowed,"now":t,"observations":[]}

class CoreTests(unittest.TestCase):
    def setUp(self):
        self.law=compile_constitution(LAW)
        self.s=genesis(self.law)
    def test_stable_debt_under_retries(self):
        a=judge(self.s,self.law,req(),ctx())
        self.assertEqual(a.verdict,"ACCEPT")
        s1=commit(self.s,a)
        debt=list(s1["obligations"].values())[0]
        s2=commit(s1,judge(s1,self.law,req("i2"),ctx(5000)))
        self.assertEqual(list(s2["obligations"].values())[0],debt)
        self.assertNotEqual(self.s,s1)
    def test_closure_not_auto_authorized(self):
        s1=commit(self.s,judge(self.s,self.law,req(),ctx()))
        v=judge(s1,self.law,req("i2","resolve"),ctx(10000))
        self.assertEqual(v.verdict,"PENDING_EXTERNAL")
        self.assertEqual(v.delta,())
    def test_no_implicit_operation(self):
        self.assertEqual(judge(self.s,self.law,req(op="alien"),ctx()).code,"LAW.NO_RULE")
    def test_permission_denied(self):
        self.assertEqual(judge(self.s,self.law,req(),ctx(allowed=False)).code,"AUTH.DENIED")
    def test_effect_does_not_dispatch(self):
        d=judge(self.s,self.law,req(op="deploy",effect=True),ctx())
        self.assertEqual(d.verdict,"ACCEPT")
        self.assertIsNotNone(d.authorization)
        self.assertIn("state_head",d.authorization)
    def test_stale_commit(self):
        d=judge(self.s,self.law,req(),ctx())
        s1=commit(self.s,d)
        with self.assertRaises(Invalid):commit(s1,d)
    def test_delta_conflict(self):
        changes=[{"key":"x","old":"not-present","new":"value"}]
        self.assertEqual(judge(self.s,self.law,req(changes=changes),ctx()).code,"DELTA.CONFLICT")
    def test_law_pin(self):
        other=compile_constitution({**LAW,"release":"v2"})
        with self.assertRaises(Invalid):judge(self.s,other,req(),ctx())
    def test_ambiguous_operation_denied(self):
        multi={**LAW,"rules":LAW["rules"]+[dict(LAW["rules"][0],id="another")]}
        c=compile_constitution(multi)
        s=genesis(c)
        self.assertEqual(judge(s,c,req(),ctx()).code,"LAW.AMBIGUOUS")
    def test_foreign_receipt_subject_rejected(self):
        bad={**ctx(),"subject":"other"}
        with self.assertRaises(Invalid):judge(self.s,self.law,req(),bad)
    def test_nondeterministic_input_rejected(self):
        bad=req(changes=[{"key":"x","old":None,"new":1.25}])
        with self.assertRaises(Invalid):judge(self.s,self.law,bad,ctx())
if __name__=="__main__":unittest.main()
