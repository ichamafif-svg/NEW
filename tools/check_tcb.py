"""Budgets, layers and independence.

Every trusted line is counted in exactly one budget, named by the guarantee it carries:
  safety         a bug can let a forbidden effect, widening or rewrite through
  restrict_only  a bug can only stop the journal (the second judge, joined by AND)
  visibility     a bug can only hide or invent a gap in health (accountability)
A module stays out of `safety` only while the structure that justifies it holds: who may import it is checked here,
the AND join is checked by tests/test_budget_classification.py. Layers: a module imports only its own layer or inner
ones; the invariants never import the code they check."""
import ast
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
spec = json.loads((root / "tcb-budget.json").read_text())
budgets = spec["budgets"]
lines = lambda path: len(path.read_text().splitlines())
tcb = {p.stem: p for p in sorted((root / "tcb").glob("*.py"))}
extra = [root / "bootstrap.py", *sorted((root / "adapters").rglob("*.py"))]
owner = {m: name for name, b in budgets.items() if isinstance(b["modules"], list) for m in b["modules"]}
problems = [f"{m} is listed in a budget but does not exist" for m in owner if m not in tcb]


def imports(path) -> set:
    found = set()
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.ImportFrom) and node.level == 1:
            found |= {node.module.split(".")[0]} if node.module else {a.name for a in node.names}
        if (isinstance(node, ast.Call) and getattr(node.func, "id", getattr(node.func, "attr", None)) == "import_module"
                and node.args and isinstance(node.args[0], ast.Constant) and str(node.args[0].value).startswith(".")):
            found.add(node.args[0].value[1:].split(".")[0])                # import_module(".x")
        if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "_NAMES" for t in node.targets):
            found |= {v.value for v in node.value.values if isinstance(v, ast.Constant)}   # lazy public table
    return found


graph = {m: imports(p) for m, p in tcb.items()}
graph["bootstrap"] = imports(root / "bootstrap.py")
for name, b in budgets.items():
    allowed = set(b.get("importers", ()))
    for m in (b["modules"] if isinstance(b["modules"], list) else []):
        for importer, used in graph.items():
            if m in used and importer != m and importer not in allowed:
                problems.append(f"{importer} imports {m} ({name}): only {sorted(allowed)} may")

layer = {m: name for name, mods in spec["layers"].items() for m in mods}
order = {name: i for i, name in enumerate(spec["layers"])}
problems += [f"{m} belongs to no layer" for m in tcb if m not in layer]
for me, used in graph.items():
    if me not in tcb:
        continue
    for other in used & set(tcb):
        if layer.get(me) != "package" and order.get(layer.get(other), 0) > order.get(layer.get(me), 0):
            problems.append(f"{me} ({layer.get(me)}) imports outward: {other} ({layer.get(other)})")
        if other in spec["independent"].get(me, []):
            problems.append(f"{me} must not import {other}")

count = {name: 0 for name in budgets}
for m, p in tcb.items():
    count[owner.get(m, "safety")] += lines(p)
count["safety"] += sum(lines(p) for p in extra)
for name, b in budgets.items():
    cap = b["max_physical_lines"]
    print(f"{name:14s} {count[name]:5d} / {cap:5d}  {'ok' if count[name] <= cap else 'EXCEEDED'}")
    if count[name] > cap:
        problems.append(f"{name} budget exceeded")
for name, mods in spec["layers"].items():
    print(f"  layer {name:16s} {sum(lines(tcb[m]) for m in mods if m in tcb):5d}")
print(f"TCB: {sum(count.values())} physical lines in total, every one counted once")
if problems:
    raise SystemExit("; ".join(problems))
