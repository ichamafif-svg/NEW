"""What happens next, for every subject in the journal: one table, from declaration to proof or withdrawal.

Rule 1: a subject exists only by the agent's signed declaration: the transition `repo:{area}:{item}/{base}/{head}`,
main moving from commit `base` to its child `head`.
Rule 4: the whole life of a subject is one table. Before its intent, its phase comes from the facts about it; after,
from the kernel's own effect automaton (floor0.LINE through `line_state`). `NEXT` gives each phase the one role that
moves it; tests check that every phase the facts and LINE can produce has an entry.
Rule 6: nothing waits forever. A subject that cannot become ready is withdrawn by the agent, which frees its target
for a new repair; a failure is a fact about one subject, never a stop for the others.

Pure functions of the journal state and a time; no I/O."""
from __future__ import annotations

from dataclasses import dataclass

from tcb.floor0 import LINE, line_state

WAIT_MS = 3 * 86_400_000                  # a subject not ready after this is withdrawn
TERMINAL = ("landed", "superseded", "unanswerable")

# phase -> (role, verb)
NEXT = {
    # before any intent, from the facts
    "measuring": ("scanner", "observe"),     # declared, its facts not all observed yet
    "ready": ("agent", "ask"),               # tests green and (reproduced or reviewed), still applicable
    "awaiting-review": ("scanner", "observe"),   # applicable and green, not reproducible: a human may review it
    "rejected": ("agent", "withdraw"),       # tests not green, or nobody reviewed it in time
    "gone": ("agent", "withdraw"),           # main moved past its base, or the world cannot answer about it
    "withdrawn": (None, "done"),
    # after an intent, the kernel's effect line
    "intended": ("guard", "issue"),
    "tokened": ("guard", "redeem"),
    "reserved": (None, "wait"),              # a guard is sending it; only the dispatch window ends this
    "expired": ("scanner", "reconcile"),
    "uncertain": ("scanner", "reconcile"),
    "proving": ("scanner", "prove"),
    "proven": (None, "done"),
    "failed": None,                          # GitHub moved nothing: back to the phase its facts give
}
LINE_STATES = {"expired"} | {to for _, to in LINE.values()} | {s for frm, _ in LINE.values() for s in frm if s}


@dataclass(frozen=True)
class Subject:
    resource: str
    area: str
    item: str
    base: str
    head: str

    @property
    def args(self) -> dict:
        return {"area": self.area, "item": self.item, "base": self.base, "head": self.head}


@dataclass(frozen=True)
class Action:
    role: str
    verb: str
    subject: Subject
    intent: str | None = None
    condition: str | None = None


def subject_of(resource: str) -> Subject | None:
    target, _, rest = resource.partition("/")
    parts, tail = target.split(":"), rest.split("/")
    if len(parts) != 3 or parts[0] != "repo" or len(tail) != 2:
        return None
    return Subject(resource, parts[1], parts[2], tail[0], tail[1])


def declared(s, agent="agent") -> list:
    """Every subject the agent declared, open or withdrawn; nothing GitHub lists can add one."""
    out = {}
    for o in s["observations"].values():
        if o["author"] == agent and o["property"] == "proposed":
            subject = subject_of(o["resource"])
            if subject:
                out[subject] = o
    return sorted(out, key=lambda x: x.resource)


def facts(s, subject: Subject, sources=("scanner",)) -> dict:
    """property -> (status, at), the latest from the given sources about this exact transition."""
    out = {}
    for o in s["observations"].values():
        if o["resource"] == subject.resource and o["author"] in sources:
            if o["property"] not in out or o["at"] > out[o["property"]][1]:
                out[o["property"]] = (o["status"], o["at"])
    return out


def latest_intent(s, subject: Subject):
    found = [it for it in s["intents"].values() if it["op"] == "remediate" and it["resource"] == subject.resource]
    return max(found, key=lambda it: it["stmt"]["at"]) if found else None


def before_intent(f: dict, review: dict, declared_at: int, since: int, now: int) -> tuple:
    """(phase, condition). After a failure (`since`), applicability must have been observed again to be believed."""
    state, at = f.get("state", (None, -1))
    if state in TERMINAL:
        return "gone", None
    if state is None or at <= since or "tests" not in f or "reproduced" not in f:
        return "measuring", None
    if f["tests"][0] != "green":
        return "rejected", None
    if f["reproduced"][0] == "yes":
        return "ready", "remediate-autonomous"
    if review.get("review", (None,))[0] == "approved":
        return "ready", "remediate-reviewed"
    return ("rejected", None) if now - declared_at > WAIT_MS else ("awaiting-review", None)


def phase(s, subject: Subject, now: int, reviewers=()) -> tuple:
    """(phase, intent id or None, condition or None) for one subject."""
    mine = facts(s, subject, ("agent",)).get("proposed", ("open", 0))
    it = latest_intent(s, subject)
    line = line_state(s["line"], it["id"], now) if it else None
    if line == "proving" and f"proof:{it['id']}" not in s["obligations"]:
        return "proven", it["id"], None
    if line not in (None, "failed"):
        return line, it["id"], None
    if mine[0] == "withdrawn":
        return "withdrawn", it and it["id"], None
    name, cond = before_intent(facts(s, subject), facts(s, subject, tuple(reviewers)), mine[1],
                               it["stmt"]["at"] if it else -1, now)
    return name, it and it["id"], cond


def plan(s, now: int, reviewers=()) -> list:
    """Every action due now, for every declared subject."""
    actions = []
    for subject in declared(s):
        name, intent, cond = phase(s, subject, now, reviewers)
        role, verb = NEXT[name]
        if role:
            actions.append(Action(role, verb, subject, intent, cond))
    return actions


def live(s, now: int, reviewers=()) -> list:
    """Subjects still addressing their target (anything not withdrawn, gone or proven)."""
    return [x for x in declared(s) if phase(s, x, now, reviewers)[0] not in ("withdrawn", "gone", "proven")]
