"""TYPE: closed shapes. A body is accepted only if every field is declared, every required field present, every value of
its declared type. Nothing unknown is ignored; it is refused.

Resources are exact names. Patterns are an exact name, '*', or a prefix that ends on a separator (':' or '/') then '*',
so a pattern never covers a sibling that merely shares letters ('repo/app*' does not exist; 'repo/app/*' does)."""
from __future__ import annotations

import re

ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:@/-]{0,127}$")
SEGMENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._@-]{0,127}$")          # no separator: safe inside a resource
DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
RESOURCE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:@/-]{0,254}$")
PATTERN = re.compile(r"^(\*|[A-Za-z0-9][A-Za-z0-9._:@/-]{0,254}[:/]\*|[A-Za-z0-9][A-Za-z0-9._:@/-]{0,254})$")
SCALARS = ("str", "int", "bool", "id", "segment", "digest")
TYPES = SCALARS + ("resource", "pattern", "list", "map")
COMMON = {"id": "id", "at": "int", "author": "id"}
FIELD = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,63}$")


class ShapeError(ValueError):
    pass


def ok(kind: str, value) -> bool:
    if kind == "str":
        return isinstance(value, str) and len(value) <= 4096
    if kind == "int":
        return isinstance(value, int) and not isinstance(value, bool)
    if kind == "bool":
        return isinstance(value, bool)
    if kind in ("id", "segment", "digest", "resource", "pattern"):
        rx = {"id": ID, "segment": SEGMENT, "digest": DIGEST, "resource": RESOURCE, "pattern": PATTERN}[kind]
        return isinstance(value, str) and bool(rx.fullmatch(value))
    if kind == "list":
        return isinstance(value, list) and len(value) <= 256
    if kind == "map":
        return isinstance(value, dict) and len(value) <= 256
    return False


def check_spec(spec, allowed=TYPES) -> None:
    if not isinstance(spec, dict) or not spec or len(spec) > 64:
        raise ShapeError("a shape is a non-empty map of field to type")
    for name, kind in spec.items():
        if name in COMMON or not FIELD.fullmatch(name) or not isinstance(kind, str) or kind.rstrip("?") not in allowed:
            raise ShapeError(f"bad field {name}: {kind}")


def build(spec: dict, body, common: bool = True) -> dict:
    """The body itself, once proven to be exactly of this shape."""
    full = {**COMMON, **spec} if common else dict(spec)
    if not isinstance(body, dict):
        raise ShapeError("a body is a map")
    unknown = set(body) - set(full)
    if unknown:
        raise ShapeError(f"undeclared fields {sorted(unknown)}")
    for name, kind in full.items():
        if name not in body:
            if not kind.endswith("?"):
                raise ShapeError(f"missing field {name}")
            continue
        if not ok(kind.rstrip("?"), body[name]):
            raise ShapeError(f"{name} is not a {kind.rstrip('?')}")
    return body


def _denotes(q: str, p: str) -> bool:
    """Every resource that pattern (or resource) p denotes is denoted by pattern q."""
    return q == p or (q.endswith("*") and p.startswith(q[:-1]))


def covers(patterns, resource: str) -> bool:
    return any(_denotes(q, resource) for q in patterns)


def within(child: list, parent: list) -> bool:
    return all(any(_denotes(q, p) for q in parent) for p in child)
