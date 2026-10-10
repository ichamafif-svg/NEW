"""Narrow Unix-domain admission gateway for an already installed K/T runtime.

The operator starts this in a protected process. Filesystem permissions, user
separation, endpoint provenance and the installed T implementations are physical
assumptions; the protocol never offers guard, signing or provider credentials.
"""
from __future__ import annotations

import json
import os
import socketserver
import stat
from pathlib import Path

from .deployment import ProductionBlocked

MAX_MESSAGE = 1_048_576


class GatewayError(ValueError):
    pass


class _Handler(socketserver.StreamRequestHandler):
    def handle(self):
        self.request.settimeout(5)
        try:
            raw = self.rfile.readline(MAX_MESSAGE + 1)
            if not raw or len(raw) > MAX_MESSAGE or not raw.endswith(b"\n"):
                raise GatewayError("REQUEST.SIZE")
            request = json.loads(raw)
            if not isinstance(request, dict) or not isinstance(request.get("action"), str):
                raise GatewayError("REQUEST.SHAPE")
            action = request["action"]
            if action == "view" and set(request) == {"action"}:
                result = self.server.deployment.constitutional_view()
            elif action == "status" and set(request) == {"action"}:
                result = self.server.deployment.status()
            elif action == "qualify" and set(request) == {"action", "required"}:
                self.server.deployment.qualify_route(request["required"])
                result = {"qualified": True}
            elif action == "admit" and set(request) == {"action", "envelope"}:
                result = self.server.deployment.admit(request["envelope"])
            else:
                raise GatewayError("REQUEST.ACTION")
            response = {"ok": True, "result": result}
        except Exception as exc:
            # A remote caller gets a refusal type, never internals of a trusted
            # process. The audit journal remains the source of admission truth.
            response = {"ok": False, "error": type(exc).__name__}
        encoded = json.dumps(response, ensure_ascii=False, separators=(",", ":")).encode()
        if len(encoded) <= MAX_MESSAGE:
            self.wfile.write(encoded + b"\n")


class AdmissionGateway(socketserver.UnixStreamServer):
    """No dispatch operation is reachable from the untrusted socket."""

    def __init__(self, path, deployment, *, mode=0o600):
        if mode not in (0o600, 0o660):
            raise GatewayError("SOCKET.MODE")
        if any(not callable(getattr(deployment, name, None)) for name in
               ("constitutional_view", "qualify_route", "admit", "status")):
            raise GatewayError("DEPLOYMENT.REQUIRED")
        target = Path(path)
        if target.exists() or target.is_symlink():
            raise GatewayError("SOCKET.EXISTS")
        parent = target.parent.stat()
        if not stat.S_ISDIR(parent.st_mode) or parent.st_mode & 0o002:
            raise GatewayError("SOCKET.UNSAFE_DIRECTORY")
        self.deployment = deployment
        self._socket_path = target
        super().__init__(str(target), _Handler)
        try:
            os.chmod(target, mode)
        except BaseException:
            self.server_close()
            raise

    def server_close(self):
        super().server_close()
        self._socket_path.unlink(missing_ok=True)
