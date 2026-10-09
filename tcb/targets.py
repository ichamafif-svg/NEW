"""Validated target contracts, used at law admission and by the read-only auditor."""
from .shapes import ID, RESOURCE


class TargetError(ValueError):
    pass


def validate(raw, rank):
    if not isinstance(raw, list) or not 2 <= len(raw) <= 128:
        raise TargetError("declare at least one coverage target and one property target (at most 128)")
    required = {"id", "kind", "resource", "property", "expect", "min_level", "fresh_ms", "due_ms", "owner", "sources"}
    targets, by_key = {}, {}
    for t in raw:
        if not isinstance(t, dict) or not required <= set(t) or set(t) - required - {"coverage", "repair", "human"}:
            raise TargetError("a target has only its declared fields")
        ident = t["id"]
        if not isinstance(ident, str) or not ID.fullmatch(ident) or ident in targets:
            raise TargetError("target IDs are unique, valid identifiers")
        if t["kind"] not in ("coverage", "property"):
            raise TargetError(f"{ident}: kind is coverage or property")
        for field in ("property", "owner"):
            if not isinstance(t[field], str) or not ID.fullmatch(t[field]):
                raise TargetError(f"{ident}: invalid {field}")
        if not isinstance(t["resource"], str) or not RESOURCE.fullmatch(t["resource"]):
            raise TargetError(f"{ident}: a target resource is exact")
        if not isinstance(t["expect"], str) or not 0 < len(t["expect"]) <= 256:
            raise TargetError(f"{ident}: expected status is a nonempty short string")
        if t["min_level"] not in rank or rank[t["min_level"]] == 0:
            raise TargetError(f"{ident}: a target needs a known positive proof level")
        if any(type(t[k]) is not int or not 0 < t[k] <= 365 * 86_400_000 for k in ("fresh_ms", "due_ms")):
            raise TargetError(f"{ident}: freshness and due time are positive bounded milliseconds")
        sources = t["sources"]
        if (not isinstance(sources, list) or not 0 < len(sources) <= 16 or len(set(sources)) != len(sources)
                or any(not isinstance(x, str) or not ID.fullmatch(x) for x in sources) or t["owner"] in sources):
            raise TargetError(f"{ident}: named sources are distinct from the owner")
        key = (t["resource"], t["property"])
        if key in by_key:
            raise TargetError(f"{ident}: another target already declares {key}")
        targets[ident], by_key[key] = dict(t), ident
    kinds = {t["kind"] for t in targets.values()}
    if kinds != {"coverage", "property"}:
        raise TargetError("coverage and property targets are both required")
    for t in targets.values():
        if t["kind"] == "property" and targets.get(t.get("coverage"), {}).get("kind") != "coverage":
            raise TargetError(f"{t['id']}: a property target names a coverage target")
        if t["kind"] == "coverage" and "coverage" in t:
            raise TargetError(f"{t['id']}: a coverage target has no parent")
    order = sorted(targets, key=lambda i: (targets[i]["kind"] != "coverage", i))   # coverage first
    return {i: targets[i] for i in order}, by_key


