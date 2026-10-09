"""Trusted provider port. Artifact computation belongs upstream of signed intents."""
import copy

from .canon import canon


class NotDispatched(ValueError):
    """The port has not entered a provider adapter."""


class EffectPort:
    def __init__(self, handlers):
        if not isinstance(handlers, dict) or not handlers or not all(callable(f) for f in handlers.values()):
            raise ValueError("explicit trusted operation adapters are required")
        self.handlers = dict(handlers)

    def perform(self, judged, expected_bytes, reservation_key):
        if canon(judged) != expected_bytes:
            raise NotDispatched("effect differs from the judged canonical bytes")
        handler = self.handlers.get(judged["op"])
        if handler is None:
            raise NotDispatched("no trusted adapter for this operation")
        try:
            return handler(judged["resource"], copy.deepcopy(judged["args"]), reservation_key)
        except Exception:
            return "unknown"             # even NotDispatched raised inside an adapter is uncertain
