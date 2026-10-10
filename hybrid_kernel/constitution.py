"""The law the kernel executes: the release's floors composed with the client's law (F0-3).
The floors come with the release and cannot be changed from a journal. The client law lives in the journal: it binds
the floor roles, adds its own declarations and may only tighten what the floors declare. `compose` enforces that rule
and the autonomy floor (every target has an autonomous repair route, or is declared human) before `Law` validates the
result. The law carries declarations and conditions; it carries no authority (authority lives in the ledger).

Kernel admission reads levels, ops, evidence, conditions and controls; accountability reads targets."""
from __future__ import annotations

import copy
import re

from . import relations as policy, obligations
from tcb.canon import CanonError, digest
from tcb.floor0 import MIN_DELAY_MS, MIN_WITNESSES, POLARITY, floor0_digest
from tcb.floors import FLOORS, ROLES, floors_digest
from tcb.targets import TargetError, validate as validate_targets
from tcb.shapes import ID, RESOURCE, SEGMENT, SCALARS, ShapeError, check_spec

from .model import check_resource_types, check_instruments

FORMAT = "standard-v0/1"
TTL = ("pending", "unredeemed", "reconcile", "proof", "observation")
DELAYS = ("rotate", "grant", "unfreeze", "law")
PLACEHOLDER = re.compile(r"\{([A-Za-z][A-Za-z0-9_]{0,63})\}")
TOP = {"format", "floor0", "levels", "ops", "evidence", "discharges", "conditions", "ttl", "delays", "witnesses",
       "controls", "targets", "obligations", "resources", "instruments"}


class LawError(ValueError):
    pass


def program(raw):
    try:
        return policy.validate(raw)
    except policy.PolicyError as exc:
        raise LawError(f"condition: {exc}") from None


def _ops(raw) -> dict:
    """An op is a closed argument shape (scalars only) and a resource template filled from separator-free arguments."""
    if not isinstance(raw, dict) or not raw:
        raise LawError("the law declares at least one op")
    ops = {}
    for name, decl in raw.items():
        if (not isinstance(name, str) or not ID.fullmatch(name) or not isinstance(decl, dict)
                or set(decl) not in ({"args", "resource", "profile"}, {"args", "resource", "profile", "trusted"})
                or decl["profile"] not in ("capability", "human_quorum")):
            raise LawError(f"op {name}: args, resource, profile and optional trusted contracts")
        trusted = decl.get("trusted", [])
        if (not isinstance(trusted, list) or len(set(map(str, trusted))) != len(trusted)
                or any(not isinstance(t, str) or t not in {f"T{i:02}" for i in range(1, 10)} for t in trusted)):
            raise LawError(f"op {name}: unknown or duplicate trusted contract")
        try:
            check_spec(decl["args"], SCALARS)
        except ShapeError as exc:
            raise LawError(f"op {name}: {exc}") from None
        template = decl["resource"]
        if not isinstance(template, str):
            raise LawError(f"op {name}: the resource is a template")
        if any(len(PLACEHOLDER.findall(p)) > 1 for p in re.split(r"[:/]", template)):
            raise LawError(f"op {name}: at most one argument slot per resource segment")
        slots = PLACEHOLDER.findall(template)
        for slot in slots:
            if decl["args"].get(slot) not in ("segment", "int"):
                raise LawError(f"op {name}: {{{slot}}} fills from a required segment or int argument")
        if not RESOURCE.fullmatch(PLACEHOLDER.sub("x", template)):
            raise LawError(f"op {name}: the template yields an exact resource")
        ops[name] = {"args": dict(decl["args"]), "resource": template, "profile": decl["profile"],
                     "trusted": sorted(set(trusted) | {"T07", "T08"})}
    return ops


CLIENT_FORMAT = "standard-client/1"
CLIENT_TOP = {"format", "floors", "bindings", "ops", "evidence", "discharges", "conditions", "targets", "obligations",
              "tighten", "ttl", "delays", "witnesses", "controls", "resources", "instruments"}
LEVEL_ORDER = {"measure": 0, "escalate": 1, "refuse": 2}


def _stricter(section: str, field: str, base, value) -> bool:
    if type(value) is not int or value <= 0 and not (section == "controls" and value == 0 and base == 0):
        return False
    if section in ("ttl",):
        return value <= base                          # shorter freshness and deadlines escalate sooner
    if section == "controls":
        return base == 0 or 0 < value <= base         # 0 means no silent-control rule: any value is stricter
    return value >= base                              # longer delays, larger witness quorum


def _reaches(op, resource: str) -> bool:
    """Invert the bounded typed template without wildcard regex or combinatorial search."""
    parts, values = re.split(r"([:/])", op["resource"]), re.split(r"([:/])", resource)
    if (len(parts) > len(values) and parts[len(values)] == "/"
            and any(PLACEHOLDER.search(p) for p in parts[len(values):])):
        parts = parts[:len(values)]                   # an op on a typed child (repo:deps:vulns/pr/7/sha) repairs its parent
    if len(parts) != len(values):
        return False
    bound = {}
    for part, value in zip(parts, values):
        slot = PLACEHOLDER.search(part)
        if slot is None:
            if part != value:
                return False
            continue
        name, left, right = slot[1], part[:slot.start()], part[slot.end():]
        if not value.startswith(left) or not value.endswith(right) or len(value) < len(left) + len(right):
            return False
        value = value[len(left):len(value) - len(right) if right else None]
        valid = bool(SEGMENT.fullmatch(value)) if op["args"][name] == "segment" else (
            bool(re.fullmatch(r"-?[0-9]{1,16}", value)) and str(int(value)) == value and abs(int(value)) <= 2 ** 53)
        if not valid or bound.get(name, value) != value:
            return False
        bound[name] = value
    return True


def compose(client) -> dict:
    """The effective release: the floors, bound to the client's identities, plus the client's own declarations.
    A client law never redefines, removes or weakens a floor."""
    if not isinstance(client, dict) or set(client) - CLIENT_TOP:
        raise LawError(f"a client law declares only {sorted(CLIENT_TOP)}")
    if client.get("format") != CLIENT_FORMAT or client.get("floors") != floors_digest():
        raise LawError("the client law is not written for the floors of this release")
    for section in ("ops", "evidence", "discharges", "conditions", "ttl", "delays", "witnesses", "controls", "tighten", "resources", "instruments"):
        if section in client and not isinstance(client[section], dict):
            raise LawError(f"{section} must be a map")
    release = copy.deepcopy(FLOORS)
    bindings = client.get("bindings")
    if (not isinstance(bindings, dict) or set(bindings) != set(ROLES)
            or not all(isinstance(v, str) and ID.fullmatch(v) for v in bindings.values())):
        raise LawError(f"bindings name an identity for each floor role {list(ROLES)}")
    bind = lambda v: bindings[v[1:]] if isinstance(v, str) and v.startswith("@") else v
    for t in release["targets"]:
        t["owner"], t["sources"] = bind(t["owner"]), [bind(x) for x in t["sources"]]
    for section in ("ops", "evidence", "discharges", "conditions", "resources", "instruments"):
        extra = client.get(section, {})
        if not isinstance(extra, dict) or set(extra) & set(release.get(section, {})):
            raise LawError(f"{section}: a client adds names, it never redefines a floor")
        release[section] = {**release.get(section, {}), **extra}
    for section in ("targets", "obligations"):
        extra = client.get(section, [])
        floor_ids = {item["id"] for item in release[section]}
        if not isinstance(extra, list) or any(not isinstance(i, dict) or i.get("id") in floor_ids for i in extra):
            raise LawError(f"{section}: a client adds entries, it never redefines a floor")
        release[section] = release[section] + extra
    for section in ("ttl", "delays", "witnesses", "controls"):
        for field, value in (client.get(section) or {}).items():
            if field not in release[section] or not _stricter(section, field, release[section][field], value):
                raise LawError(f"{section}.{field}: a client may only tighten the floors")
            release[section][field] = value
    tighten = client.get("tighten") or {}
    if not isinstance(tighten, dict) or set(tighten) - {"targets", "obligations", "ops"}:
        raise LawError("tighten lists floor targets and obligations")
    if any(not isinstance(v, dict) for v in tighten.values()):
        raise LawError("tighten sections must be maps")
    for op, change in tighten.get("ops", {}).items():
        if (op not in FLOORS["ops"] or not isinstance(change, dict) or not change
                or set(change) - {"profile", "trusted"}
                or ("profile" in change and change["profile"] != "human_quorum")):
            raise LawError("tighten.ops only raises a floor profile or adds trusted contracts")
        if "profile" in change:
            release["ops"][op]["profile"] = "human_quorum"
        if "trusted" in change:
            base = release["ops"][op].get("trusted", [])
            release["ops"][op]["trusted"] = sorted(set(base) | set(change["trusted"])) if isinstance(change["trusted"], list) else change["trusted"]
    rank = {name: i for i, name in enumerate(release["levels"])}
    floor_proof = max(rank[d["min_level"]] for rules in FLOORS["discharges"].values() for d in rules)
    if any(not isinstance(d, dict) or rank.get(d.get("min_level"), -1) < floor_proof
           for rules in (client.get("discharges") or {}).values() for d in (rules if isinstance(rules, list) else [None])):
        raise LawError("discharges: a client adds ways to prove, never at a lower level than the floors")
    floor_targets = {t["id"]: t for t in release["targets"][:len(FLOORS["targets"])]}
    for section in tighten:
        if not isinstance(tighten[section], dict):
            raise LawError(f"tighten.{section} must be a map")
    for tid, change in (tighten.get("targets") or {}).items():
        t = floor_targets.get(tid)
        if t is None or not isinstance(change, dict) or set(change) - {"min_level", "fresh_ms", "due_ms"}:
            raise LawError(f"tighten: {tid} is not a floor target or the change is unknown")
        if "min_level" in change and (change["min_level"] not in rank or rank[change["min_level"]] < rank[t["min_level"]]):
            raise LawError(f"tighten: {tid}.min_level may only rise")
        for k in ("fresh_ms", "due_ms"):
            if k in change and not (type(change[k]) is int and 0 < change[k] <= t[k]):
                raise LawError(f"tighten: {tid}.{k} may only shorten")
        t.update(change)
    floor_obl = {o["id"]: o for o in release["obligations"][:len(FLOORS["obligations"])]}
    for oid, change in (tighten.get("obligations") or {}).items():
        o = floor_obl.get(oid)
        if o is None or not isinstance(change, dict) or set(change) - {"level", "due_ms"}:
            raise LawError(f"tighten: {oid} is not a floor obligation or the change is unknown")
        if "level" in change and LEVEL_ORDER.get(change["level"], -1) < LEVEL_ORDER[o["level"]]:
            raise LawError(f"tighten: {oid}.level may only rise")
        if "due_ms" in change and not (type(change["due_ms"]) is int and 0 < change["due_ms"] <= o["due_ms"]):
            raise LawError(f"tighten: {oid}.due_ms may only shorten")
        o.update(change)
    release["ops"] = _ops(release["ops"])
    for t in release["targets"]:                      # the autonomy floor
        if not isinstance(t, dict):
            raise LawError("a target is a map")
        human, repair = t.get("human"), t.get("repair")
        if human is True and repair is None:
            continue
        op = release["ops"].get(repair) if isinstance(repair, str) else None
        if human is not None or op is None or not isinstance(t.get("resource"), str) or not _reaches(op, t["resource"]):
            raise LawError(f"F1: target {t.get('id')} needs an op of this law that can repair its resource, "
                           "or an explicit human declaration")
    return release


class Law:
    def __init__(self, release: dict, pinned: str):
        # Verify the same snapshot that will be used throughout this kernel.
        release = copy.deepcopy(release)
        try:
            actual = digest(release)
        except CanonError as exc:
            raise LawError(f"the release is not canonical: {exc}") from None
        if actual != pinned:
            raise LawError("the release law is not the one this kernel pins")
        if not isinstance(release, dict) or set(release) - TOP:
            raise LawError(f"the release declares only {sorted(TOP)}")
        if release.get("format") != FORMAT or release.get("floor0") != floor0_digest():
            raise LawError("the law does not declare this FLOOR-0")
        self.digest, self.release = pinned, release
        self.levels = release.get("levels")
        if (not isinstance(self.levels, list) or not self.levels or self.levels[0] != "unknown"
                or len(set(self.levels)) != len(self.levels) or not all(isinstance(x, str) and ID.fullmatch(x) for x in self.levels)):
            raise LawError("levels are an ordered list of names starting at unknown")
        self.rank = {name: i for i, name in enumerate(self.levels)}
        try:
            self.resources = check_resource_types(release.get("resources", {}), program)
            self.instruments = check_instruments(release.get("instruments", {}), self.rank)
        except ValueError as exc:
            raise LawError(str(exc)) from None
        try:
            self.targets, self.by_key = validate_targets(release.get("targets"), self.rank)
        except TargetError as exc:
            raise LawError(str(exc)) from None
        self.ops = _ops(release.get("ops"))
        self.evidence = {}
        for name, decl in (release.get("evidence") or {}).items():
            if name in POLARITY or not ID.fullmatch(name) or not isinstance(decl, dict) or set(decl) != {"fields"}:
                raise LawError(f"evidence {name}: a new name with {{fields}}")
            fields = decl["fields"]
            try:
                check_spec(fields)
            except ShapeError as exc:
                raise LawError(f"evidence {name}: {exc}") from None
            if fields.get("under") != "id" or fields.get("resource") != "resource" or fields.get("level", "str") != "str":
                raise LawError(f"evidence {name}: names its capability (under), its exact resource, a str level")
            self.evidence[name] = dict(fields)
        self.discharges = {}
        for kind, rules in (release.get("discharges") or {}).items():
            if kind not in self.evidence or "level" not in self.evidence[kind] or not isinstance(rules, list):
                raise LawError(f"discharges: {kind} is not an evidence kind with a level")
            for d in rules:
                if (not isinstance(d, dict) or set(d) != {"obligation", "key", "min_level"} or d["obligation"] != "proof"
                        or d["min_level"] not in self.rank or self.evidence[kind].get(d["key"]) != "id"):
                    raise LawError(f"discharges of {kind}: {d}")
            self.discharges[kind] = rules
        self.conditions = {}
        for name, rules in (release.get("conditions") or {}).items():
            if not ID.fullmatch(name):
                raise LawError(f"condition name {name}")
            self.conditions[name] = program(rules)
        self.ttl = release.get("ttl")
        if (not isinstance(self.ttl, dict) or set(self.ttl) != set(TTL)
                or not all(type(v) is int and v > 0 for v in self.ttl.values())):
            raise LawError(f"ttl declares exactly {TTL}")
        self.delay = release.get("delays")
        if (not isinstance(self.delay, dict) or set(self.delay) != set(DELAYS)
                or any(type(v) is not int or v < MIN_DELAY_MS for v in self.delay.values())):
            raise LawError(f"delays declares exactly {DELAYS}, each at least FLOOR-0's minimum")
        witnesses = release.get("witnesses")
        if (not isinstance(witnesses, dict) or set(witnesses) != {"quorum"}
                or type(witnesses["quorum"]) is not int or witnesses["quorum"] < MIN_WITNESSES):
            raise LawError(f"witnesses declares a quorum of at least {MIN_WITNESSES}")
        self.witness_quorum = witnesses["quorum"]
        controls = release.get("controls")
        if not isinstance(controls, dict) or set(controls) != {"heartbeat_ms"} or type(controls["heartbeat_ms"]) is not int or controls["heartbeat_ms"] < 0:
            raise LawError("controls declares heartbeat_ms (0: no silent-control rule)")
        self.heartbeat_ms = controls["heartbeat_ms"]
        try:
            self.obligations = obligations.validate(release.get("obligations"), {**POLARITY, **dict.fromkeys(self.evidence, "attest")},
                                                    program)
        except obligations.DeclarationError as exc:
            raise LawError(f"obligations: {exc}") from None

    def resource_of(self, op: str, args: dict) -> str:
        """The resource an effect touches is derived from its arguments, never declared beside them (F0-9)."""
        return PLACEHOLDER.sub(lambda m: str(args[m.group(1)]), self.ops[op]["resource"])

