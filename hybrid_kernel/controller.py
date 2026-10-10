"""Operator loop; the U gateway never exposes a guard or provider port."""
from __future__ import annotations

from .gateway import AdmissionGateway


class TrustedController:
    def __init__(self, deployment, *, guard_identity, guard_signer, socket_path, socket_mode=0o660):
        self.deployment, self.guard_identity, self.guard_signer = deployment, guard_identity, guard_signer
        self.gateway = AdmissionGateway(socket_path, deployment, mode=socket_mode)
        self.gateway.timeout = 1

    def cycle(self):
        """One bounded pass; failures of one route do not invent success."""
        status = {}
        for name, call in (("effects", lambda: self.deployment.dispatch_due(
                            identity=self.guard_identity, signer=self.guard_signer)),
                           ("reconciliation", self.deployment.reconcile_due),
                           ("escalation", self.deployment.deliver_due)):
            try:
                status[name] = call()
            except Exception as exc:
                status[name] = {"blocked": type(exc).__name__}
        return status

    def serve(self):
        """Handle U requests and retry due operator work on every tick."""
        while True:
            self.gateway.handle_request()
            self.cycle()

    def close(self):
        self.gateway.server_close()
        self.deployment.close()
