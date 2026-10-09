"""The floors: what Standard imposes on every client, shipped with the release and covered by the code digest.

FLOOR-0 (floor0.py) guards the TCB itself. The floors carry the direction (autonomy, security, compliance) in the
same language as a client law, so that every requirement can produce a measurable gap: autonomy is the distance
between what the floors and the client require and what the repository has.

Only the Standard team changes this file, by a release. A client law never redefines, removes or weakens anything
declared here: it binds the floor roles to its own identities, adds its own declarations, and may only tighten.
Context-dependent requirements apply to every client through conditions on attested facts, never by opting out."""
from .canon import digest
from .floor0 import MIN_DELAY_MS, floor0_digest

FORMAT = "standard-floors/1"
ROLES = ("owner", "inventory_source")          # identities every client binds to its own root

FLOORS = {
    "format": "standard-v0/1",
    "floor0": floor0_digest(),
    "levels": ["unknown", "real"],
    "ttl": {"pending": 86_400_000, "unredeemed": 86_400_000, "reconcile": 86_400_000, "proof": 86_400_000,
            "observation": 86_400_000},
    "delays": {"rotate": MIN_DELAY_MS, "grant": MIN_DELAY_MS, "unfreeze": MIN_DELAY_MS, "law": MIN_DELAY_MS},
    "witnesses": {"quorum": 2},
    "controls": {"heartbeat_ms": 0},
    # F1: closure on independent proof. Every effect leaves a proof obligation that only independent evidence closes.
    "evidence": {"evidence": {"fields": {"under": "id", "resource": "resource", "subject": "id", "level": "str"}}},
    "discharges": {"evidence": [{"obligation": "proof", "key": "subject", "min_level": "real"}]},
    # A maintenance class every client receives: dependency updates from the dependency bot.
    "ops": {"merge": {"args": {"pr": "segment", "method": "str"}, "resource": "repo:pr:{pr}", "profile": "capability"},
            "inventory-refresh": {"args": {"scope": "segment"}, "resource": "repo:inventory:{scope}",
                                  "profile": "capability"}},
    "conditions": {"bot-author": {"all": [{"observed": ["pr_author", "dependabot[bot]", "real"]}]}},
    # F2: coverage. The declared universe must be observed complete by an independent source, or it is a gap.
    "targets": [
        {"id": "inventory", "kind": "coverage", "resource": "repo:inventory:all", "property": "coverage",
         "expect": "complete", "min_level": "real", "fresh_ms": 86_400_000, "due_ms": 86_400_000,
         "owner": "@owner", "sources": ["@inventory_source"], "repair": "inventory-refresh"},
    ],
    "obligations": [],
}


def floors_digest() -> str:
    return digest({"format": FORMAT, "floors": FLOORS, "roles": list(ROLES)})
