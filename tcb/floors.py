"""The floors: what Standard imposes on every client, shipped with the release and covered by the code digest.

FLOOR-0 (floor0.py) guards the TCB itself. The floors carry the direction (autonomy, security, compliance) in the
same language as a client law, so that every requirement can produce a measurable gap: autonomy is the distance
between what the floors and the client require and what the repository has.

Only the Standard team changes this file, by a release. A client law never redefines, removes or weakens anything
declared here: it binds the floor roles to its own identities, adds its own declarations, and may only tighten.
Context-dependent requirements apply to every client through conditions on attested facts, never by opting out.

Two families of measures. Technical measures are observed by the independent scanner and repaired by agents through
`remediate`, whose resource is the exact commit of a pull request under the target it repairs. Organisational measures
are attested by the compliance officer, a human, and have no automatic repair: their gap goes to people. Which
ISO 27001, NIS2 and DORA control each measure evidences is a projection outside the TCB (compliance/catalog.json)."""
from .canon import digest
from .floor0 import MIN_DELAY_MS, floor0_digest

FORMAT = "standard-floors/2"
ROLES = ("owner", "inventory_source", "scanner", "compliance_officer")   # every client binds them to its own root
DAY = 86_400_000

# Technical: (id, resource, property, expect, fresh, due). Observed by @scanner, repaired by `remediate`.
TECHNICAL = [
    ("vulns", "repo:deps:vulns", "high", "none", 1, 7),
    ("deps-age", "repo:deps:age", "major_behind", "none", 7, 30),
    ("licenses", "repo:deps:licenses", "policy", "compliant", 7, 30),
    ("secrets", "repo:code:secrets", "leaks", "none", 1, 1),
    ("sast", "repo:code:sast", "high", "none", 1, 30),
    ("ci", "repo:ci:main", "status", "green", 1, 2),
    ("actions", "repo:ci:actions", "pinned", "all", 7, 30),
    ("sbom", "repo:supply:sbom", "state", "current", 7, 7),
]
# Settings the scanner observes but no pull request can change: their gap goes to people.
SETTINGS = [("branch", "repo:settings:main", "protection", "pr-and-checks", 1, 7)]
# Organisational: (id, resource, fresh) attested "current" by @compliance_officer under the statement of applicability.
ORGANISATIONAL = [
    ("isms", "org:isms:policy", 365), ("risk", "org:risk:assessment", 365), ("access", "org:access:review", 90),
    ("training", "org:people:training", 365), ("hr", "org:people:hr", 365), ("suppliers", "org:supply:register", 365),
    ("incident", "org:incident:procedure", 365), ("continuity", "org:continuity:test", 365),
    ("backup", "org:backup:restore", 90), ("legal", "org:legal:register", 365), ("audit", "org:audit:independent", 365),
    ("physical", "org:physical:sites", 365), ("crypto", "org:crypto:policy", 365),
    ("resilience", "org:resilience:testing", 365), ("assets", "org:assets:register", 365),
    ("infra", "org:infra:baseline", 180), ("monitoring", "org:ops:monitoring", 180), ("threat", "org:threat:intel", 180),
]


def _target(ident, resource, prop, expect, fresh, due, coverage, source, **extra):
    return {"id": ident, "kind": "property", "coverage": coverage, "resource": resource, "property": prop,
            "expect": expect, "min_level": "real", "fresh_ms": fresh * DAY, "due_ms": due * DAY, "owner": "@owner",
            "sources": [source], **extra}


FLOORS = {
    "format": "standard-v0/1",
    "floor0": floor0_digest(),
    "levels": ["unknown", "real"],
    "ttl": {"pending": DAY, "unredeemed": DAY, "reconcile": DAY, "proof": DAY, "observation": DAY},
    "delays": {"rotate": MIN_DELAY_MS, "grant": MIN_DELAY_MS, "unfreeze": MIN_DELAY_MS, "law": MIN_DELAY_MS},
    "witnesses": {"quorum": 2},
    "controls": {"heartbeat_ms": 0},
    # F1: closure on independent proof. Every effect leaves a proof obligation that only independent evidence closes.
    "evidence": {"evidence": {"fields": {"under": "id", "resource": "resource", "subject": "id", "level": "str"}}},
    "discharges": {"evidence": [{"obligation": "proof", "key": "subject", "min_level": "real"}]},
    "ops": {"merge": {"args": {"pr": "segment", "method": "str"}, "resource": "repo:pr:{pr}", "profile": "capability"},
            "inventory-refresh": {"args": {"scope": "segment"}, "resource": "repo:inventory:{scope}",
                                  "profile": "capability"},
            # Merge one exact commit of a pull request that repairs repo:{area}:{item}. Facts that authorize it are
            # observed on this very resource, so they bind the commit that will be merged.
            "remediate": {"args": {"area": "segment", "item": "segment", "pr": "segment", "head": "segment", "method": "str"},
                    "resource": "repo:{area}:{item}/pr/{pr}/{head}", "profile": "capability"}},
    "conditions": {"bot-author": {"all": [{"observed": ["pr_author", "dependabot[bot]", "real"]}]},
                   # Autonomy: a green, dependency-only commit; anything else needs an independent human review.
                   "remediate-autonomous": {"all": [{"observed": ["ci", "green", "real"]},
                                              {"observed": ["scope", "dependencies", "real"]}]},
                   "remediate-reviewed": {"all": [{"observed": ["ci", "green", "real"]},
                                            {"observed": ["review", "approved", "real"]}]}},
    # F2: coverage. Each declared universe must be observed complete by an independent source, or it is a gap.
    "targets": [
        {"id": "inventory", "kind": "coverage", "resource": "repo:inventory:all", "property": "coverage",
         "expect": "complete", "min_level": "real", "fresh_ms": DAY, "due_ms": DAY,
         "owner": "@owner", "sources": ["@inventory_source"], "repair": "inventory-refresh"},
        {"id": "soa", "kind": "coverage", "resource": "org:controls:soa", "property": "coverage",
         "expect": "complete", "min_level": "real", "fresh_ms": 365 * DAY, "due_ms": 30 * DAY,
         "owner": "@owner", "sources": ["@compliance_officer"], "human": True},
        *(_target(*t, "inventory", "@scanner", repair="remediate") for t in TECHNICAL),
        *(_target(*t, "inventory", "@scanner", human=True) for t in SETTINGS),
        *(_target(i, r, "attested", "current", f, 30, "soa", "@compliance_officer", human=True)
          for i, r, f in ORGANISATIONAL),
    ],
    "obligations": [],
}


def floors_digest() -> str:
    return digest({"format": FORMAT, "floors": FLOORS, "roles": list(ROLES)})
