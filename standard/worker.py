"""Unprivileged external worker protocol; no provider credentials or guard API."""
from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass

from .client import GatewayClient
from .service import WorkError


@dataclass(frozen=True)
class Worker:
    route: str
    command: tuple[str, ...]
    cwd: str
    timeout: int = 600

    def __post_init__(self):
        if (not self.route or not isinstance(self.command, tuple) or not self.command
                or any(not isinstance(x, str) or not x for x in self.command)
                or not self.cwd or type(self.timeout) is not int or not 1 <= self.timeout <= 3600):
            raise WorkError("invalid worker specification")


def run_once(engine, workers, *, mode, now, backoff_ms=60_000):
    """Prepare one signed candidate in U; K/T decide admission independently.

    This runner requires the socket proxy so callbacks cannot access an in-
    process deployment. It is still the installation's job to isolate the
    worker OS user and its filesystem/network permissions from the operator.
    """
    if (not isinstance(engine.service._deployment, GatewayClient)
            or type(now) is not int or now < 0 or type(backoff_ms) is not int or backoff_ms <= 0):
        raise WorkError("worker requires a separate K/T gateway and valid schedule")
    cycle = engine.sync(mode=mode)
    lease = engine.claim(mode=mode, now=now)
    if lease is None:
        return {"status": "IDLE"}
    task = next(t for t in cycle["tasks"] if t["id"] == lease["id"])
    available = {r["id"] for r in task["routes"] if r["state"] == "AVAILABLE"}
    selected = next((w for w in workers if w.route in available), None)
    status = "NO_WORKER"
    try:
        if selected is not None:
            payload = json.dumps({"task": task, "basis": lease["basis"], "law": cycle["law"]},
                                 ensure_ascii=False)
            # The worker receives only law and a work proposal. Its own
            # unprivileged signing identity may be available in its OS domain.
            env = {key: os.environ[key] for key in ("PATH", "LANG") if key in os.environ}
            process = subprocess.run(selected.command, input=payload, text=True,
                                     capture_output=True, cwd=selected.cwd, env=env,
                                     timeout=selected.timeout, check=True)
            if len(process.stdout) > 1_048_576:
                raise WorkError("worker response too large")
            envelope = json.loads(process.stdout)["envelope"]
            engine.service.submit(mode=mode, task_id=task["id"], route_id=selected.route,
                                  basis=lease["basis"], envelope=envelope)
            status = "SUBMITTED"
    except Exception:
        status = "RETRY"
    finally:
        engine.complete_attempt(mode=mode, task_id=lease["id"],
                                lease_until=lease["lease_until"], next_at=now + backoff_ms)
    return {"status": status, "task": task["id"], "attempt": lease["attempt"],
            "obligation_closed": False}
