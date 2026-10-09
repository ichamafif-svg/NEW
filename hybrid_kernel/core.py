"""Hybrid constitutional decision core: pure judgment + required delta + lasting debts.

Non-privileged prototype. The caller MUST supply an externally authenticated
admission context. This module never signs, sends effects or creates authority.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from tcb.canon import canon, digest, CanonError
from tcb.policy import validate as validate_policy, evaluate as evaluate_policy, PolicyError

MAX_RULES=128
MAX_CHANGES=256
MAX_OBLIGATIONS=4096
MAX_FACTS=4096
MAX_BYTES=1<<20

class Invalid(ValueError):
    pass

@dataclass(frozen=True)
class Decision:
    verdict:str
    code:str
    before:str
    after:str|None
    delta:tuple
    obligations:tuple
    authorization:dict|None

    def wire(self):
        return {"verdict":self.verdict,"code":self.code,"before":self.before,
                "after":self.after,"delta":list(self.delta),"obligations":list(self.obligations),
                "authorization":self.authorization}

def _canonical(value):
    try:
        encoded=canon(value)
        if len(encoded)>MAX_BYTES:raise Invalid("LIMIT.BYTES")
        return encoded
    except (CanonError,RecursionError,TypeError) as ex:
        raise Invalid("TYPE.CANON") from ex

def _shape(record, fields):
    return isinstance(record,dict) and set(record)==set(fields)

def _require(test,why):
    if not test:raise Invalid(why)

def compile_constitution(raw):
    """Finite positive constraints; no executable callbacks or implicit defaults.

    Each rule has scope: a generic operation string, optional request condition
    and obligations to open/close. Rule statements only come from pinned law.
    """
    _canonical(raw)
    _require(_shape(raw,("release","rules","max_due_ms")),"LAW.SHAPE")
    _require(isinstance(raw["release"],str) and raw["release"],"LAW.RELEASE")
    _require(type(raw["max_due_ms"]) is int and 0<raw["max_due_ms"]<=365*86400000,"LAW.DUE")
    rules=raw["rules"]
    _require(isinstance(rules,list) and len(rules)<=MAX_RULES,"LAW.RULE_LIMIT")
    ids=set()
    for rule in rules:
        _require(_shape(rule,("id","operation","requires","opens","closes","effect")),"LAW.RULE_SHAPE")
        _require(isinstance(rule["id"],str) and rule["id"] and rule["id"] not in ids,"LAW.ID")
        ids.add(rule["id"])
        _require(isinstance(rule["operation"],str) and rule["operation"],"LAW.OP")
        _require(type(rule["effect"]) is bool,"LAW.EFFECT")
        try:validate_policy(rule["requires"])
        except (PolicyError,ValueError) as ex:raise Invalid("LAW.POLICY") from ex
        for field in ("opens","closes"):
            _require(isinstance(rule[field],list) and len(rule[field])<=16,"LAW.OBLIGATIONS")
            for spec in rule[field]:
                _require(_shape(spec,("kind","key_field")),"LAW.OBLIGATION_SHAPE")
                _require(isinstance(spec["kind"],str) and spec["kind"],"LAW.OBLIGATION_KIND")
                _require(isinstance(spec["key_field"],str) and spec["key_field"] in ("subject","resource"),"LAW.KEY_FIELD")
    return {"pinned":digest(raw),"raw":raw}

def genesis(constitution):
    return {"epoch":0,"law":constitution["pinned"],"objects":{},"obligations":{},
            "authorizations":{},"head":digest({"genesis":constitution["pinned"]})}

def _key(kind,subject):
    return digest([kind,subject])

def _decision(state,verdict,code,delta=(),after=None,obligations=(),authorization=None):
    return Decision(verdict,code,digest(state),after,tuple(delta),tuple(obligations),authorization)

def judge(state,constitution,request,context):
    """Return a verdict; NEVER mutate state. Caller authenticates context via T.

    context is a receipt from trusted boundary: exact subject, permission,
    qualified observations and immutable evaluation time. This method checks
    receipt-to-request binding, but cannot prove the receipt itself is authentic.
    A privileged effect may only be dispatched by a separately fenced T port.
    """
    _canonical(state);_canonical(request);_canonical(context)
    _require(_shape(state,("epoch","law","objects","obligations","authorizations","head")),"STATE.SHAPE")
    _require(state["law"]==constitution["pinned"],"LAW.PIN")
    _require(_shape(request,("id","operation","subject","resource","changes","effect")),"REQ.SHAPE")
    _require(_shape(context,("receipt","subject","allowed","now","observations")),"CONTEXT.SHAPE")
    _require(type(context["allowed"]) is bool and type(context["now"]) is int and context["now"]>=0,"CONTEXT.TYPE")
    _require(isinstance(context["receipt"],str) and context["receipt"],"CONTEXT.RECEIPT")
    _require(context["subject"]==request["subject"],"CONTEXT.SUBJECT")
    _require(isinstance(context["observations"],list) and len(context["observations"])<=MAX_FACTS,"CONTEXT.FACTS")
    _require(isinstance(request["id"],str) and request["id"],"REQ.ID")
    _require(isinstance(request["operation"],str) and isinstance(request["subject"],str) and isinstance(request["resource"],str),"REQ.TYPE")
    _require(type(request["effect"]) is bool,"REQ.EFFECT")
    _require(isinstance(request["changes"],list) and len(request["changes"])<=MAX_CHANGES,"REQ.CHANGES")
    if not context["allowed"]:return _decision(state,"REJECT","AUTH.DENIED")
    # Every change must have explicit old and new values. No silent mutation.
    before_objects=state["objects"]
    new_objects=dict(before_objects)
    touched=set()
    for change in request["changes"]:
        _require(_shape(change,("key","old","new")),"DELTA.SHAPE")
        key=change["key"]
        _require(isinstance(key,str) and key and key not in touched,"DELTA.KEY")
        touched.add(key)
        if before_objects.get(key)!=change["old"] or (key not in before_objects and change["old"] is not None):
            return _decision(state,"REJECT","DELTA.CONFLICT")
        if change["new"] is None:new_objects.pop(key,None)
        else:new_objects[key]=change["new"]
    applicable=[rule for rule in constitution["raw"]["rules"] if rule["operation"]==request["operation"]]
    if not applicable:return _decision(state,"REJECT","LAW.NO_RULE")
    if len(applicable)!=1:return _decision(state,"REJECT","LAW.AMBIGUOUS")
    rule=applicable[0]
    if request["effect"]!=rule["effect"]:return _decision(state,"REJECT","EFFECT.MISMATCH")
    try:
        approved=evaluate_policy(validate_policy(rule["requires"]),
            request=request, observations=tuple(tuple(row) for row in context["observations"]),
            opened=tuple((ob["kind"],ob["subject"]) for ob in state["obligations"].values()),
            closed=())
    except (PolicyError,ValueError,TypeError):
        return _decision(state,"REJECT","EVIDENCE.INVALID")
    if not approved:return _decision(state,"REJECT","LAW.UNSATISFIED")
    # A closing request alone cannot prove satisfaction. Qualified closure must
    # be established by an independent verifier and explicitly bound to receipt.
    if rule["closes"]:return _decision(state,"PENDING_EXTERNAL","OBL.CLOSURE_PROOF_REQUIRED")
    obligations=dict(state["obligations"])
    for spec in rule["opens"]:
        subject=request[spec["key_field"]]
        ident=_key(spec["kind"],subject)
        if ident not in obligations:
            _require(len(obligations)<MAX_OBLIGATIONS,"OBL.LIMIT")
            obligations[ident]={"kind":spec["kind"],"subject":subject,
                                "opened":context["now"],
                                "due":context["now"]+constitution["raw"]["max_due_ms"]}
    # No deletion of an open obligation is permitted through arbitrary object changes.
    old_obligations=state["obligations"]
    next_state={"epoch":state["epoch"]+1,"law":state["law"],"objects":new_objects,
         "obligations":obligations,"authorizations":dict(state["authorizations"]),"head":""}
    authorization=None
    if rule["effect"]:
        authorization={"request_digest":digest(request),"receipt_digest":digest(context),
                       "law":state["law"],"state_head":state["head"]}
        next_state["authorizations"][request["id"]]=authorization
    next_state["head"]=digest({"previous":state["head"],"request":request,"receipt":context,
                               "epoch":next_state["epoch"],"objects":new_objects,
                               "obligations":obligations,"authorizations":next_state["authorizations"]})
    delta=[{"set":"objects","value":new_objects},{"set":"obligations","value":obligations},
           {"set":"authorizations","value":next_state["authorizations"]},
           {"set":"epoch","value":next_state["epoch"]},{"set":"head","value":next_state["head"]}]
    return _decision(state,"ACCEPT","OK",delta,digest(next_state),tuple(sorted(obligations)),authorization)

def commit(state,decision):
    """Apply only exactly the admitted delta, refusing stale or fabricated decisions.

    The caller must obtain decision from judge in the same trusted process; this
    function is not an authenticated persistence or compare-and-swap primitive.
    """
    _canonical(state)
    _require(decision.verdict=="ACCEPT" and digest(state)==decision.before,"COMMIT.STALE")
    _require(len(decision.delta)==5,"COMMIT.DELTA")
    expected=("objects","obligations","authorizations","epoch","head")
    _require(tuple(d.get("set") for d in decision.delta)==expected,"COMMIT.SHAPE")
    result=dict(state)
    for row in decision.delta:result[row["set"]]=row["value"]
    _require(digest(result)==decision.after,"COMMIT.DIGEST")
    return result
