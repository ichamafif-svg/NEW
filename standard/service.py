"""Project constitutional debt into work and admit signed proposals via K/T.

Routes are installed by the operator. Discovery and planning do not grant rights.
The service has no provider credentials, signing keys or independent effect path.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass
from fnmatch import fnmatchcase

from hybrid_kernel.deployment import ProductionBlocked
from hybrid_kernel.constitution import PLACEHOLDER
from tcb.crypto import EnvelopeError, open_envelope


class WorkError(ValueError):
    pass


NEEDS = frozenset({"cover", "observe", "repair", "prove", "reconcile", "build"})
ROLES = frozenset(f"T{i:02}" for i in range(1, 10))


@dataclass(frozen=True)
class Route:
    """Operator-provisioned capability declaration; never a physical assessment."""

    id: str
    mode: str
    resource: str
    needs: frozenset[str]
    required_t: frozenset[str] = frozenset()

    def __post_init__(self):
        if (not isinstance(self.id, str) or not self.id or not isinstance(self.resource, str)
                or not self.resource or self.mode not in {"BUILD", "RUN", "BOTH"}
                or not isinstance(self.needs, frozenset) or not self.needs
                or not self.needs <= NEEDS or not isinstance(self.required_t, frozenset)
                or not self.required_t <= ROLES):
            raise WorkError("invalid installed route")


def _matches(route, mode, resource, need):
    return (route.mode in (mode, "BOTH") and need in route.needs
            and fnmatchcase(resource, route.resource))


def _law_trust(law, resource, need):
    """Minimum physical contracts are derived from the pinned effective law.

    An installed route may demand more contracts; it cannot subtract these.
    Preparation of repository changes is a provider write, even before a
    constitutional intent moves main.
    """
    required = {"T06"} if need in {"cover", "observe", "prove"} else set()
    if need == "reconcile":
        required.add("T08")
    if need in {"repair", "build"}:
        required |= {"T07", "T08"}
        for target in law.get("targets", []):
            if target.get("resource") == resource and target.get("repair"):
                op = law.get("ops", {}).get(target["repair"], {})
                required.update(op.get("trusted", []))
    return required


def _fits_task(law, task, envelope):
    try:
        kind, body, _, _ = open_envelope(envelope)
        resource, need = task["resource"], task["need"]
        if need in {"cover", "observe"}:
            return kind in {"observation", "measurement"} and body.get("resource") == resource
        if need == "prove":
            return kind in {"evidence", *law.get("evidence", {})} and body.get("resource") == resource
        if need in {"repair", "build"} and kind == "intent":
            op = law.get("ops", {}).get(body.get("op"))
            args = body.get("args")
            if not op or not isinstance(args, dict):
                return False
            declared = PLACEHOLDER.sub(lambda match: str(args[match.group(1)]), op["resource"])
            return any(t.get("resource") == resource and t.get("repair") == body["op"]
                       for t in law.get("targets", [])) and (declared == resource or declared.startswith(resource + "/"))
        # Reconciliation belongs to the independent T08 operator pass.
        return False
    except (EnvelopeError, KeyError, TypeError, ValueError, AttributeError):
        return False


class StandardService:
    """One law-based work surface for BUILD and RUN.

    The deployment owns the physical trust check and constitutional admission.
    A caller may submit only an independently signed statement; it never receives
    an allow token or a privileged provider port from this service.
    """

    def __init__(self, deployment, routes=()):
        if any(not callable(getattr(deployment, name, None)) for name in
               ("constitutional_view", "qualify_route", "admit")):
            raise WorkError("a governed K/T deployment is required")
        routes = tuple(routes)
        if any(not isinstance(r, Route) for r in routes) or len({r.id for r in routes}) != len(routes):
            raise WorkError("routes must have distinct installed identities")
        self._deployment = deployment
        self._routes = routes

    def inspect(self, *, mode="RUN"):
        if mode not in {"BUILD", "RUN"}:
            raise WorkError("unknown operating mode")
        view = self._deployment.constitutional_view()
        basis = copy.deepcopy(view["basis"])
        work = view["work"]
        if work["status"] == "BLOCKED":
            raise WorkError("constitutional audit is unavailable")
        inventory = []
        for route in sorted(self._routes, key=lambda r: r.id):
            try:
                self._deployment.qualify_route(route.required_t)
                state = "AVAILABLE"
            except ProductionBlocked:
                state = "TRUST_BLOCKED"
            inventory.append({"id": route.id, "mode": route.mode, "resource": route.resource,
                              "needs": sorted(route.needs), "required_t": sorted(route.required_t),
                              "state": state})
        by_route = {row["id"]: row for row in inventory}
        tasks = []
        for obligation in work["work"] + work["human"]:
            subject = obligation.get("subject")
            resource = obligation.get("resource") or (subject.split("|", 1)[0] if isinstance(subject, str) else None)
            if not resource:
                resource = "system:" + obligation["obligation"]
            if not isinstance(resource, str):
                raise WorkError("obligation has no exact subject")
            needs = obligation.get("steps", []) if obligation.get("next") == "propose_work" else []
            if mode == "BUILD":
                needs = ["build" if need == "repair" else need for need in needs]
            if not needs:
                needs = ["reconcile"] if obligation.get("type") == "effect" else []
            for need in needs:
                candidates = sorted((r for r in self._routes if _matches(r, mode, resource, need)),
                                    key=lambda r: r.id)
                choices = []
                for route in candidates:
                    required = route.required_t | _law_trust(view["law"], resource, need)
                    state = by_route[route.id]["state"]
                    if state == "AVAILABLE":
                        try:
                            self._deployment.qualify_route(required)
                        except ProductionBlocked:
                            state = "TRUST_BLOCKED"
                    choices.append({"id": route.id, "state": state, "required_t": sorted(required)})
                tasks.append({"id": f"{obligation['obligation']}:{need}",
                              "obligation": obligation["obligation"], "resource": resource,
                              "due": obligation["due"], "need": need, "routes": choices,
                              "state": "READY" if any(c["state"] == "AVAILABLE" for c in choices)
                              else ("TRUST_BLOCKED" if choices else "NO_ROUTE")})
            if obligation.get("next") == "human_review" and not needs:
                tasks.append({"id": f"{obligation['obligation']}:review",
                              "obligation": obligation["obligation"], "resource": resource,
                              "due": obligation["due"], "need": "review", "routes": [],
                              "state": "HUMAN_REVIEW"})
        tasks.sort(key=lambda t: (t["due"], t["id"]))
        qualification = [{"id": "qualify:" + r["id"], "route": r["id"],
                          "required_t": r["required_t"],
                          "closure": "independent_live_qualification"}
                         for r in inventory if r["state"] == "TRUST_BLOCKED"]
        qualification += [{"id": "qualify:" + choice["id"] + ":" + task["id"],
                           "route": choice["id"], "task": task["id"],
                           "required_t": choice["required_t"],
                           "closure": "independent_live_qualification"}
                          for task in tasks for choice in task["routes"]
                          if choice["state"] == "TRUST_BLOCKED"
                          and by_route[choice["id"]]["state"] == "AVAILABLE"]
        return {"format": "standard-cycle/1", "mode": mode, "read_only": True,
                "basis": basis, "law": copy.deepcopy(view["law"]), "tasks": tasks,
                "routes": inventory,
                "qualification_work": qualification,
                "audit_state": work["status"]}

    def submit(self, *, mode, task_id, route_id, basis, envelope):
        """Recheck the current prefix and route before forwarding signed bytes to K."""
        current = self.inspect(mode=mode)
        if current["basis"] != basis:
            raise WorkError("work belongs to an older constitutional prefix")
        task = next((t for t in current["tasks"] if t["id"] == task_id), None)
        if task is None or not any(r["id"] == route_id and r["state"] == "AVAILABLE"
                                   for r in task["routes"]):
            raise WorkError("work has no qualified installed route")
        if not isinstance(envelope, dict):
            raise WorkError("an independently signed statement is required")
        if not _fits_task(current["law"], task, envelope):
            raise WorkError("signed statement does not address this exact constitutional task")
        return self._deployment.admit(envelope)
