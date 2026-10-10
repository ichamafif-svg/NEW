"""Read-only, prefix-bound working context for agents and operators.

This is a projection, not a grant or an assessment authority. The kernel owns
the effective law; release qualification is a separate, explicitly unverified
source. A mismatched health view must never be presented as current work.
"""
from __future__ import annotations

import copy

from tcb.canon import digest
from .planner import plan


class ViewError(ValueError):
    pass


def agent_view(kernel, snapshot, health, *, readiness=None):
    state = copy.deepcopy(snapshot)
    verdict = copy.deepcopy(health)
    if (not isinstance(state, dict) or not isinstance(verdict, dict)
            or type(state.get("size")) is not int or state["size"] < 1
            or state.get("head") != verdict.get("head")
            or state["size"] != verdict.get("size")):
        raise ViewError("health and constitutional law must name the same prefix")
    work = plan(verdict)
    if work["status"] == "BLOCKED":
        raise ViewError("the audit cannot supply current work")
    law = kernel.law_of(state)
    effective = copy.deepcopy(law.release)
    if digest(effective) != state["law"]["digest"]:
        raise ViewError("the effective law differs from its constitutional pin")
    gaps = []
    if readiness is not None:
        if (not isinstance(readiness, dict) or readiness.get("schema") != "standard.hybrid.release-readiness/v1"
                or not isinstance(readiness.get("criteria"), list)):
            raise ViewError("unknown release qualification format")
        for row in readiness["criteria"]:
            if (not isinstance(row, dict) or not isinstance(row.get("id"), str)
                    or not row["id"].startswith("T") or not row["id"][1:].isdigit()):
                continue
            if row.get("verified") is not True:
                gaps.append({"contract": row["id"], "status": row.get("status", "UNKNOWN"),
                             "route": "independent_qualification"})
    return {"format": "standard-agent-constitution/1", "read_only": True,
            "basis": {"genesis": state["domain"], "head": state["head"], "size": state["size"],
                      "law_digest": law.digest, "code_digest": state["code"]},
            "law": effective, "work": work, "trust_gaps": sorted(gaps, key=lambda row: row["contract"]),
            "trust_work": [{"id": "qualify:" + row["contract"], "contract": row["contract"],
                            "next": "propose_implementation_and_evidence",
                            "closure": "independent_qualification"} for row in sorted(gaps, key=lambda row: row["contract"])],
            "trust_gap_source": "release_inventory_not_live_provider_evidence"}
