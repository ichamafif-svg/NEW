"""Trusted launch point: verify an externally selected code digest before importing TCB."""
import hashlib
import importlib.abc
import importlib.machinery
import importlib.metadata
import json
import platform
import re
import os
import stat
import sys
from pathlib import Path


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def manifest(root):
    root = Path(root).resolve()
    paths = [root / "bootstrap.py", *sorted((root / "tcb").rglob("*.py")),
             *sorted((root / "adapters").rglob("*.py")),
             *sorted((root / "hybrid_kernel").rglob("*.py"))]
    return {"format": "tcb-code/1", "files": {
        p.relative_to(root).as_posix(): "sha256:" + hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        "runtime": {"python": sys.version, "implementation": sys.implementation.name,
                    "machine": platform.machine(), "cryptography": importlib.metadata.version("cryptography")}}


def verified(root, expected):
    value = manifest(root)
    actual = "sha256:" + hashlib.sha256(encoded(value)).hexdigest()
    if actual != expected:
        raise ValueError("code manifest differs from the external pin")
    return value


class SourceLoader(importlib.machinery.SourceFileLoader):
    def get_code(self, fullname):
        return self.source_to_code(self.get_data(self.path), self.path)


class SourceFinder(importlib.abc.MetaPathFinder):
    def __init__(self, root, files):
        self.root, self.files = root, files

    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".")[0] not in ("tcb", "adapters", "hybrid_kernel"):
            return None
        spec = importlib.machinery.PathFinder.find_spec(fullname, path)
        if spec is None or not spec.origin or not spec.origin.endswith(".py"):
            raise ImportError("TCB imports must come from verified Python source")
        relative = Path(spec.origin).resolve().relative_to(self.root).as_posix()
        if relative not in self.files:
            raise ImportError("module is outside the pinned code manifest")
        spec.loader = SourceLoader(fullname, spec.origin)
        return spec


def main():
    root = Path(__file__).resolve().parent
    code_pin = sys.argv[1]
    release = verified(root, code_pin)
    sys.modules["bootstrap"] = sys.modules[__name__]
    sys.path.insert(0, str(root))
    sys.meta_path.insert(0, SourceFinder(root, release["files"]))
    sys.dont_write_bytecode = True
    if sys.argv[2] == "--verify":
        print(code_pin)
    elif sys.argv[2] == "--worker":
        from tcb.worker import main as worker_main
        worker_main(sys.argv[3], code_pin)
    elif sys.argv[2] == "--health":
        from tcb import Auditor, Journal, Kernel, SQLitePins
        from tcb.canon import parse, canon
        cfg = parse(Path(sys.argv[3]).read_bytes())
        kernel = Kernel(code_pin=code_pin)
        with Journal(cfg["journal"], kernel, genesis_pin=cfg["genesis_pin"],
                     checkpoints=SQLitePins(cfg["pins"]), accountability=Auditor()) as journal:
            print(canon(journal.health(required_at=cfg.get("required_at"))).decode())
    elif sys.argv[2] == "--control":
        # Deployment-specific operator code must be part of this exact release
        # manifest and loaded only after source verification, before secrets.
        name, config = sys.argv[3:5]
        if not re.fullmatch(r"adapters\.[a-z][a-z0-9_]*", name):
            raise ValueError("operator module must be a pinned adapter")
        path = name.replace(".", "/") + ".py"
        if path not in release["files"]:
            raise ValueError("operator module absent from the release")
        meta = os.stat(config, follow_symlinks=False)
        if not stat.S_ISREG(meta.st_mode) or meta.st_uid != os.getuid() or meta.st_mode & 0o077:
            raise ValueError("operator configuration must be owner-only")
        import importlib
        module = importlib.import_module(name)
        module.serve(json.loads(Path(config).read_text()))
    else:
        raise ValueError("expected --verify, --worker MODE, --health CONFIG or --control ADAPTER CONFIG")


if __name__ == "__main__":
    main()
