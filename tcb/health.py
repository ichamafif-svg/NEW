"""Layer 3, accountability: replay the journal in a confined worker and return the health verdict.

It reads the journal through its read-only interface and never writes. It is injected into the journal from outside
(the journal never imports this layer). A failure here produces FAULT; it can never authorize anything."""
from __future__ import annotations

import threading
import time

from .canon import raw_digest, parse
from .sandbox import StreamWorker, WorkerFault


class Auditor:
    def __init__(self):
        self._lock, self._worker = threading.RLock(), None

    def close(self):
        with self._lock:
            if self._worker is not None:
                self._worker.close()
                self._worker = None

    def health(self, journal, *, required_at=None, timeout=30, prefix=False) -> dict:
        """Stream only missing signed entries; a restarted worker replays from genesis."""
        as_of, head = None, None
        deadline = time.monotonic() + timeout

        def request(packet):
            left = deadline - time.monotonic()
            if left <= 0:
                raise WorkerFault("health reconstruction timed out")
            worker.timeout = min(left, 30)
            return worker.request(packet)

        with self._lock:
            try:
                view = journal.prefix()
                as_of, head, size, retained = view["as_of"], view["head"], view["size"], view["retained"]
                if not retained:
                    raise WorkerFault("no retained checkpoints")
                worker = self._worker
                cursor = worker.size if worker is not None else 0
                if cursor > size or (cursor and view["heads"][cursor - 1] != worker.head):
                    raise WorkerFault("worker prefix diverged")
                if worker is None or worker.child.poll() is not None:
                    self.close()
                    worker = self._worker = StreamWorker(journal.kernel.code_pin)
                    if request({"op": "init", "genesis_pin": journal.genesis_pin}) != {"size": 0, "head": None}:
                        raise WorkerFault("invalid worker initialization")
                while worker.size < size:
                    rows = journal.raw_rows(worker.size, size)
                    if not rows:
                        raise WorkerFault("journal changed during streaming")
                    for raw in rows:
                        ack = request({"op": "entry", "entry": parse(raw)})
                        if ack != {"size": worker.size + 1, "head": raw_digest(raw)}:
                            raise WorkerFault("invalid worker entry acknowledgment")
                        worker.size, worker.head = ack["size"], ack["head"]
                verdict = request({"op": "health", "checkpoints": retained, "required_at": required_at})
                current = journal.retained()
                if not prefix and current != retained:
                    raise WorkerFault("retained checkpoints advanced during audit")
                if max((c["size"] for c in current), default=0) < max((c["size"] for c in retained), default=0):
                    raise WorkerFault("retained checkpoints regressed during audit")
                if (not isinstance(verdict, dict) or verdict.get("state") not in ("PROVEN", "IN_PROGRESS", "ESCALATED")
                        or verdict.get("as_of") != as_of or verdict.get("head") != head or verdict.get("size") != size):
                    raise WorkerFault("invalid health verdict")
                return {**verdict, "current": current == retained} if prefix else verdict
            except (WorkerFault, ValueError, OSError) as exc:
                self.close()
                return {"state": "FAULT", "fault": str(exc), "as_of": as_of, "head": head}
