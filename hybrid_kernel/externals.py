"""Trusted External capability contracts and fail-closed registration.

A capability declaration is NOT a safety proof. Production admission requires
independently assessed implementation evidence, authenticated by the operator.
The nine contracts are roles, not mandatory nine services.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Protocol, Mapping, Any
from tcb.canon import digest, canon

class ContractError(ValueError):
    pass

class Status(str,Enum):
    VERIFIED="VERIFIED"
    REJECTED="REJECTED"
    UNAVAILABLE="UNAVAILABLE"
    INDETERMINATE="INDETERMINATE"

CONTRACTS=frozenset(f"T{i:02}" for i in range(1,10))

@dataclass(frozen=True)
class Capability:
    contract_id:str
    provider_id:str
    trust_domain:str
    version:str
    evidence_digest:str
    status:Status
    expires_at:int
    verified_at:int

    def __post_init__(self):
        if self.contract_id not in CONTRACTS:
            raise ContractError("CONTRACT.UNKNOWN")
        for s in (self.provider_id,self.trust_domain,self.version):
            if not isinstance(s,str) or not s:
                raise ContractError("CONTRACT.IDENTITY")
        if not isinstance(self.evidence_digest,str) or not self.evidence_digest.startswith("sha256:"):
            raise ContractError("CONTRACT.EVIDENCE")
        if type(self.verified_at) is not int or type(self.expires_at) is not int or self.expires_at<=self.verified_at:
            raise ContractError("CONTRACT.TIME")
        if not isinstance(self.status,Status):
            raise ContractError("CONTRACT.STATUS")

class CapabilityRegistry:
    """An operator-pinned catalog; no self-attestation by adapters.

    Registry construction is a trusted provisioning operation, NOT a function
    agents may call. VERIFIED only means recorded assessment within validity;
    evidence authenticity and physical separation must be checked externally.
    """
    def __init__(self, capabilities, *, required=CONTRACTS):
        cap=list(capabilities)
        if not isinstance(required,(tuple,list,set,frozenset)) or not set(required)<=CONTRACTS:
            raise ContractError("CONTRACT.REQUIRED")
        if len(cap)>len(CONTRACTS):
            raise ContractError("CONTRACT.COUNT")
        slots={}
        for item in cap:
            if not isinstance(item,Capability) or item.contract_id in slots:
                raise ContractError("CONTRACT.DUPLICATE_OR_TYPE")
            slots[item.contract_id]=item
        self._slots=slots
        self.required=frozenset(required)

    def validate(self, now:int):
        if type(now) is not int or now<0:raise ContractError("CONTRACT.CLOCK")
        problems=[]
        for name in sorted(self.required):
            c=self._slots.get(name)
            if c is None:problems.append((name,"ABSENT"))
            elif c.status is not Status.VERIFIED:problems.append((name,c.status.value))
            elif c.expires_at<=now:problems.append((name,"EXPIRED"))
        if problems:raise ContractError("CONTRACT.FAIL_CLOSED:"+repr(problems))
        return True

    def inventory(self):
        return tuple(self._slots[k] for k in sorted(self._slots))

class PinPort(Protocol):
    def bind(self,genesis:str)->None:...
    def load(self)->list[dict]:...
    def retain(self,pin:dict)->None:...
    def halted(self)->str|None:...

class AdmissionPort(Protocol):
    def admit(self,envelope:dict):...
    def snapshot(self):...

class EffectGuardPort(Protocol):
    def issue(self,intent_id:str,at:int,cosigners=()):...
    def redeem(self,token_id:str,at:int):...

class EvidencePort(Protocol):
    def qualify(self,claim:Mapping[str,Any]):...

class ClockPort(Protocol):
    def attest(self,subject:str)->Mapping[str,Any]:...

class IndependentJudgePort(Protocol):
    def check(self,state:Mapping[str,Any],entry:Mapping[str,Any],decision:Mapping[str,Any]):...
