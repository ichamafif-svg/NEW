"""Canonical JSON: one value, one byte string. Floats, NaN, non-string keys, duplicate keys and invalid Unicode do not
exist here. Every failure is a CanonError; nothing else escapes."""
from __future__ import annotations

import hashlib
import json

MAX_DEPTH = 32
MAX_INT = 2 ** 53


class CanonError(ValueError):
    pass


def _text(value: str) -> None:
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        raise CanonError("strings are valid Unicode") from None


def _check(value, depth: int = 0) -> None:
    if depth > MAX_DEPTH:
        raise CanonError("nested too deep")
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, str):
        return _text(value)
    if isinstance(value, int):
        if abs(value) > MAX_INT:
            raise CanonError("integer out of range")
        return
    if isinstance(value, list):
        for item in value:
            _check(item, depth + 1)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise CanonError("object keys are strings")
            _text(key)
            _check(item, depth + 1)
        return
    raise CanonError(f"{type(value).__name__} is not canonical JSON")


def canon(value) -> bytes:
    _check(value)
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def digest(value) -> str:
    return "sha256:" + hashlib.sha256(canon(value)).hexdigest()


def raw_digest(raw: bytes) -> str:
    """The digest of a value whose canonical bytes are `raw`."""
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _refuse(token):
    raise CanonError(f"{token} is not canonical JSON")


def parse(raw: bytes, *, max_bytes=1 << 20):
    """Bytes to value, only if the bytes are exactly the canonical encoding of that value."""
    def pairs(items):
        out = {}
        for key, item in items:
            if key in out:
                raise CanonError(f"duplicate key {key!r}")
            out[key] = item
        return out
    if not isinstance(raw, (bytes, bytearray)) or len(raw) > max_bytes:
        raise CanonError(f"at most {max_bytes} bytes")
    try:
        value = json.loads(raw, object_pairs_hook=pairs, parse_float=_refuse, parse_constant=_refuse)
    except CanonError:
        raise
    except (ValueError, RecursionError) as exc:      # JSONDecodeError, Unicode, oversized integers, depth
        raise CanonError(str(exc)[:200]) from None
    if canon(value) != raw:
        raise CanonError("bytes are not the canonical encoding")
    return value
