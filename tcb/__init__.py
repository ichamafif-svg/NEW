"""Public names are loaded on use; admission does not import health or adapters."""
from importlib import import_module

_NAMES = {
    "Accountability": "accountability", "Guard": "guard", "Kernel": "kernel", "Refused": "kernel",
    "apply": "kernel", "empty": "kernel", "Journal": "ledger", "audit": "ledger", "entry": "ledger",
    "rollback_problems": "ledger", "SQLitePins": "pins", "EffectPort": "effects", "NotDispatched": "effects",
    "Auditor": "health",
}
__all__ = list(_NAMES)


def __getattr__(name):
    if name not in _NAMES:
        raise AttributeError(name)
    value = getattr(import_module("." + _NAMES[name], __name__), name)
    globals()[name] = value
    return value
