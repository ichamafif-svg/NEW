"""Unprivileged Standard work client; requires an installed K/T gateway."""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from . import GatewayClient, Route, StandardService, WorkEngine
from .dashboard import render, render_fault
from .discovery import discover_repository
from .worker import Worker, run_once
from hybrid_kernel.deployment import ProductionBlocked


def load_service(path):
    cfg = json.loads(Path(path).read_text())
    if not isinstance(cfg, dict) or not {"socket", "work_db", "routes"} <= set(cfg) or set(cfg) - {"socket", "work_db", "routes", "workers"}:
        raise ValueError("configuration requires socket, work_db and routes")
    routes = []
    for raw in cfg["routes"]:
        if not isinstance(raw, dict) or set(raw) != {"id", "mode", "resource", "needs", "required_t"}:
            raise ValueError("invalid route declaration")
        routes.append(Route(raw["id"], raw["mode"], raw["resource"],
                            frozenset(raw["needs"]), frozenset(raw["required_t"])))
    workers = [Worker(w["route"], tuple(w["command"]), w["cwd"], w.get("timeout", 600))
               for w in cfg.get("workers", [])]
    return StandardService(GatewayClient(cfg["socket"]), routes), cfg["work_db"], workers


def fault_status(service):
    try:
        return service._deployment.status()
    except ProductionBlocked:
        return {"state": "FAULT", "basis": None, "reason": "GATEWAY_UNAVAILABLE"}


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python -m standard")
    parser.add_argument("command", choices=("discover", "status", "claim", "submit", "attempt", "run", "watch", "dashboard"))
    parser.add_argument("--config", help="unprivileged work configuration")
    parser.add_argument("--mode", choices=("BUILD", "RUN"), default="RUN")
    parser.add_argument("--repo", help="repository path for read-only discovery")
    parser.add_argument("--input", help="JSON with the claim, signed envelope and selected route")
    parser.add_argument("--output", help="dashboard HTML path")
    parser.add_argument("--interval", type=int, default=60, help="watch interval in seconds")
    args = parser.parse_args(argv)
    if args.command == "discover":
        if not args.repo: parser.error("discover requires --repo")
        result = discover_repository(args.repo)
    else:
        if not args.config: parser.error("this command requires --config")
        service, work_db, workers = load_service(args.config)
        engine = WorkEngine(work_db, service)
        try:
            if args.command == "status":
                try:
                    result = engine.sync(mode=args.mode)
                except ProductionBlocked:
                    result = fault_status(service)
            elif args.command == "claim":
                cycle = engine.sync(mode=args.mode)
                claim = engine.claim(mode=args.mode, now=int(time.time() * 1000))
                task = next((t for t in cycle["tasks"] if claim and t["id"] == claim["id"]), None)
                result = {"claim": claim, "task": task, "law": cycle["law"] if task else None}
            elif args.command == "run":
                result = run_once(engine, workers, mode=args.mode, now=int(time.time() * 1000))
            elif args.command == "watch":
                if not 1 <= args.interval <= 3600: parser.error("watch interval must be 1..3600 seconds")
                while True:
                    try:
                        result = run_once(engine, workers, mode=args.mode, now=int(time.time() * 1000))
                    except ProductionBlocked:
                        result = fault_status(service)
                    print(json.dumps(result, ensure_ascii=False), flush=True)
                    time.sleep(args.interval)
            elif args.command == "dashboard":
                if not args.output: parser.error("dashboard requires --output")
                try:
                    cycle = engine.sync(mode=args.mode)
                    discovery = discover_repository(args.repo) if args.repo else None
                    content, status = render(cycle, discovery), {"head": cycle["basis"]["head"]}
                except ProductionBlocked:
                    status = fault_status(service)
                    content = render_fault(status)
                Path(args.output).write_text(content, encoding="utf-8")
                result = {"dashboard": str(Path(args.output).resolve()), **status}
            elif args.command in ("submit", "attempt"):
                if not args.input: parser.error("submit and attempt require --input")
                request = json.loads(Path(args.input).read_text())
                now = int(time.time() * 1000)
                if args.command == "submit":
                    service.submit(mode=args.mode, task_id=request["task_id"],
                                   route_id=request["route_id"], basis=request["basis"],
                                   envelope=request["envelope"])
                engine.complete_attempt(mode=args.mode, task_id=request["task_id"],
                                        lease_until=request["lease_until"],
                                        next_at=now + int(request.get("retry_ms", 60_000)))
                result = {"status": "SUBMITTED" if args.command == "submit" else "ATTEMPT_RECORDED",
                          "task": request["task_id"], "obligation_closed": False}
        finally:
            engine.close()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
