"""Authenticated admission boundary using the existing DSSE/Ed25519 verifier.

The receipt signer is a trusted external verifier; its key must come from an
independently pinned trust root, never from the untrusted incoming request.
"""
from __future__ import annotations
from tcb.canon import digest
from tcb.crypto import open_envelope, verify, EnvelopeError
from .core import judge, Invalid

def judge_signed(state,constitution,request,envelope,trust_root):
    """Fail closed unless one pinned trusted key signs the exact admission context.

    No reusable bearer capability is issued here. Authorization is for one
    request digest, state head and law pin at a specified trusted time.
    Replay/fencing/durable commit remain external production blockers.
    """
    try:
        if not isinstance(trust_root,dict) or set(trust_root)!={"key","signer","domain"}:
            raise Invalid("TRUST.ROOT")
        kind,body,message,subject=open_envelope(envelope)
        if kind!="hybrid-admission":raise Invalid("TRUST.KIND")
        if subject!=f'{trust_root["domain"]}/hybrid-admission:{body.get("id")}':
            raise Invalid("TRUST.DOMAIN")
        if not isinstance(envelope["signatures"],list) or len(envelope["signatures"])!=1:
            raise Invalid("TRUST.SIGNER_COUNT")
        sig=envelope["signatures"][0]
        if sig["keyid"]!=trust_root["signer"] or trust_root["key"].get("keyid")!=sig["keyid"]:
            raise Invalid("TRUST.SIGNER")
        if not verify(trust_root["key"],message,sig):raise Invalid("TRUST.SIGNATURE")
        fields={"id","request_digest","state_head","law","subject","allowed","now","observations"}
        if not isinstance(body,dict) or set(body)!=fields:raise Invalid("TRUST.BODY")
        if (body["request_digest"]!=digest(request) or
            body["state_head"]!=state["head"] or
            body["law"]!=constitution["pinned"] or
            body["subject"]!=request["subject"]):
            raise Invalid("TRUST.BINDING")
        context={"receipt":digest(envelope),"subject":body["subject"],"allowed":body["allowed"],
                "now":body["now"],"observations":body["observations"]}
        return judge(state,constitution,request,context)
    except (EnvelopeError,KeyError,TypeError,ValueError) as ex:
        if isinstance(ex,Invalid):raise
        raise Invalid("TRUST.INVALID_ENVELOPE") from ex
