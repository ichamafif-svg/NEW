"""Unprivileged U-side proxy for the K/T Unix-domain admission gateway."""
from __future__ import annotations

import json
import socket

from hybrid_kernel.deployment import ProductionBlocked


class GatewayClient:
    def __init__(self, path, *, timeout=15):
        self.path, self.timeout = str(path), timeout

    def _call(self, request):
        data = json.dumps(request, separators=(",", ":"), ensure_ascii=False).encode() + b"\n"
        if len(data) > 1_048_576:
            raise ProductionBlocked("GATEWAY.REQUEST_TOO_LARGE")
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                client.settimeout(self.timeout)
                client.connect(self.path)
                client.sendall(data)
                with client.makefile("rb") as stream:
                    raw = stream.readline(1_048_577)
            if not raw or len(raw) > 1_048_576 or not raw.endswith(b"\n"):
                raise ProductionBlocked("GATEWAY.RESPONSE")
            response = json.loads(raw)
        except (OSError, ValueError) as exc:
            raise ProductionBlocked("GATEWAY.UNAVAILABLE") from exc
        if not isinstance(response, dict) or response.get("ok") is not True:
            raise ProductionBlocked("GATEWAY.REFUSED")
        return response["result"]

    def constitutional_view(self):
        return self._call({"action": "view"})

    def status(self):
        return self._call({"action": "status"})

    def qualify_route(self, required):
        self._call({"action": "qualify", "required": sorted(required)})

    def admit(self, envelope):
        return self._call({"action": "admit", "envelope": envelope})
