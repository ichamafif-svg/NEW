"""Compatibility import; the sole implementation is hybrid_kernel.core."""
import sys
from importlib import import_module
sys.modules[__name__] = import_module("hybrid_kernel.core")
