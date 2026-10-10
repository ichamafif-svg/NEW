"""Finite positive policies. The sealed law owns names; delegates never submit programs.
Admission supplies only facts already checked for freshness and independence."""
from __future__ import annotations

import re
from collections.abc import Mapping

NAME = re.compile(r"[a-z][a-z0-9_-]{0,63}\Z")
PATH = re.compile(r"[A-Za-z][A-Za-z0-9_]{0,63}(?:\.[A-Za-z][A-Za-z0-9_]{0,63})?\Z")
ATOM = {"eq", "prefix", "observed", "closed_at_least", "open", "related"}
MAX_ATOMS = 16
MAX_FACTS = 20_000


class PolicyError(ValueError):
    pass


def validate(policy):
    """Returns immutable atoms after exact-shape checking; no recursion, joins or inline code."""
    if not isinstance(policy, dict) or set(policy) != {"all"} or not isinstance(policy["all"], list):
        raise PolicyError("policy is {all: [atoms]}")
    if not 0 < len(policy["all"]) <= MAX_ATOMS:
        raise PolicyError("policy must have 1..16 predicates")
    result = []
    for atom in policy["all"]:
        if not isinstance(atom, dict) or len(atom) != 1:
            raise PolicyError("each predicate has one known operator")
        op, args = next(iter(atom.items()))
        if op not in ATOM or not isinstance(args, list) or len(args) != (3 if op in ("observed", "related") else 2):
            raise PolicyError("unknown predicate or arity")
        if op in ("eq", "prefix", "open"):
            if not isinstance(args[0 if op != "open" else 1], str) or not PATH.fullmatch(args[0 if op != "open" else 1]):
                raise PolicyError("unknown request field")
        if op == "closed_at_least":
            if type(args[1]) is not int or not 1 <= args[1] <= MAX_FACTS:
                raise PolicyError("count must be positive and bounded")
        if not all(type(arg) in (str, int) and (type(arg) is int or len(arg) <= 128) for arg in args):
            raise PolicyError("only bounded scalar arguments are allowed")
        if op == "prefix" and (not isinstance(args[1], str) or not args[1]):
            raise PolicyError("prefix must be a nonempty string")
        if op == "eq" and type(args[1]) not in (str, int):
            raise PolicyError("eq uses a typed scalar")
        if op in ("observed", "closed_at_least", "open") and (not isinstance(args[0], str) or not NAME.fullmatch(args[0])):
            raise PolicyError("the fact kind is a pinned name")
        if op == "related":
            from .model import RELATIONS
            if args[0] not in RELATIONS or not all(isinstance(a, str) for a in args):
                raise PolicyError("related uses a closed typed relation")
            if any(a.startswith("$") and a not in ("$author", "$resource", "$under") for a in args[1:]):
                raise PolicyError("relation bindings are author, resource, under")
        result.append((op, tuple(args)))
    return tuple(result)


def evaluate(atoms, *, request, observations=(), closed=(), opened=(), relations=()):
    """Evaluate against already verified and independent facts. Missing or malformed facts deny."""
    if any(len(rows) > MAX_FACTS for rows in (observations, closed, opened, relations)):
        raise PolicyError("fact set exceeds its configured limit")
    if (not isinstance(request, dict)
            or any(not isinstance(row, tuple) or len(row) != 4 for row in observations)
            or any(not isinstance(row, tuple) or len(row) != 2 for rows in (closed, opened) for row in rows)
            or any(not isinstance(row, tuple) or len(row) != 3 for row in relations)):
        raise PolicyError("request or fact set is malformed")

    def field(path):
        value = request
        for part in path.split("."):
            value = value.get(part) if isinstance(value, Mapping) else None
        return value

    for op, args in atoms:
        if op == "eq":
            value = field(args[0])
            ok = type(value) is type(args[1]) and value == args[1]
        elif op == "prefix":
            value = field(args[0])
            ok = isinstance(value, str) and value.startswith(args[1])
        elif op == "observed":
            ok = (request.get("resource"), *args) in observations
        elif op == "related":
            name, left, right = args
            resolve = lambda x: request.get(x[1:]) if x.startswith("$") else x
            ok = (name, resolve(left), resolve(right)) in relations
        elif op == "closed_at_least":
            ok = len({key for kind, key in closed if kind == args[0]}) >= args[1]
        elif op == "open":
            value = field(args[1])
            ok = type(value) in (str, int) and (args[0], value) in opened
        else:
            raise PolicyError("unknown predicate")
        if not ok:
            return False
    return True
