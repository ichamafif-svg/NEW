"""Offline read-only projection of an audit JSON, without journal access."""
import json
import sys
from .planner import plan

result = plan(json.load(sys.stdin))
print(json.dumps(result, ensure_ascii=False, indent=2))
raise SystemExit(1 if result["status"] == "BLOCKED" else 0)
