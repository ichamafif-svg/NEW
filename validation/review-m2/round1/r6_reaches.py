"""R6: `_reaches` child rule. Any op whose template has a '/' child below a matching prefix now 'reaches' the parent:
a client op `{x}/noop` satisfies the F1 autonomy floor for every single-segment target, and
`repo:{a}:{b}/pr/{pr}/{head}` for every repo:A:B target, whatever it measures. Authority is unaffected
(evidence and conditions use the exact intent resource); only the structural route claim is widened."""
from ops.cycle import law
from tcb.law import compose, _ops, _reaches

ops = _ops({"noop": {"args": {"x": "segment"}, "resource": "{x}/noop", "profile": "capability"}})
print("{x}/noop reaches 'billing':", _reaches(ops["noop"], "billing"), "| 'payroll':", _reaches(ops["noop"], "payroll"))
client = law()
client["ops"] = {"noop": {"args": {"x": "segment"}, "resource": "{x}/noop", "profile": "capability"}}
client["targets"] = [{"id": "payroll-encrypted", "kind": "property", "resource": "payroll", "property": "encrypted",
                      "expect": "yes", "min_level": "real", "fresh_ms": 86_400_000, "due_ms": 86_400_000,
                      "owner": "icham", "sources": ["scanner"], "repair": "noop"}]
try:
    compose(client)
    print("compose accepted target 'payroll' with autonomous route 'noop' ({x}/noop)")
except Exception as exc:  # noqa: BLE001
    print("compose refused:", exc)
