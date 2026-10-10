"""Trusted installation assembly; all physical ports come from the operator.

No local defaults are substituted for missing custody, independent assessment,
fenced effect dispatch, readback or durable restoration anchors.
"""
from __future__ import annotations

from .assessment import SignedAssessmentBoundary
from .controller import TrustedController
from .deployment import GovernedDeployment, ProductionBlocked, EFFECT


def install(*, ledger_path, pin_store, genesis_pin, assessment_bundle,
            pinned_assessors, trusted_now, effect_port, reconciliation_port,
            guard_identity, guard_signer, socket_path, delivery_port=None,
            socket_mode=0o660):
    """Assemble the operator-owned service after an external constitution ceremony.

    The signed assessment establishes authenticated claims, not their physical
    truth. The operator is responsible for independent tests of their premises,
    runtime isolation, and socket/pin/credential custody.
    """
    if (effect_port is None or reconciliation_port is None or not guard_identity
            or guard_signer is None or not pinned_assessors):
        raise ProductionBlocked("INSTALL.MISSING_PHYSICAL_PORT")
    boundary = SignedAssessmentBoundary(assessment_bundle, pinned_assessors)
    deployment = GovernedDeployment(
        ledger_path=ledger_path, pin_store=pin_store, genesis_pin=genesis_pin,
        trust_boundary=boundary, trusted_now=trusted_now, effect_port=effect_port,
        reconciliation_port=reconciliation_port, delivery_port=delivery_port)
    try:
        deployment.qualify_route(EFFECT)
        deployment.guard(identity=guard_identity, signer=guard_signer)
        return TrustedController(deployment, guard_identity=guard_identity,
                                 guard_signer=guard_signer, socket_path=socket_path,
                                 socket_mode=socket_mode)
    except BaseException:
        deployment.close()
        raise
