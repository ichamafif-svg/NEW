"""Local code identity; production imports must go through the trusted bootstrap."""
from pathlib import Path

from .canon import digest


def code_digest():
    # bootstrap deliberately has no dependency on any tcb module.
    import bootstrap
    return digest(bootstrap.manifest(Path(__file__).resolve().parents[1]))
