"""Standard's single constitutional judgment and explicit trusted boundaries."""
from importlib import import_module

_NAMES = {
    "Kernel": "core", "Refused": "core", "Decision": "model",
    "ConstitutionalRuntime": "runtime", "IntegrationError": "runtime",
    "GovernedDeployment": "deployment", "ProductionBlocked": "deployment",
    "Capability": "externals", "CapabilityRegistry": "externals",
    "ContractError": "externals", "Status": "externals",
}
__all__ = list(_NAMES)

def __getattr__(name):
    if name not in _NAMES:
        raise AttributeError(name)
    value = getattr(import_module("." + _NAMES[name], __name__), name)
    globals()[name] = value
    return value
