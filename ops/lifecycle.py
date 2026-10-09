"""What happens next, for every subject in the journal, derived from the kernel's own effect automaton.

Principle (cause 4 of the M2 review): the untrusted roles do not keep a lifecycle of their own. A subject is a commit
the agent declared in the journal; its effect line is the kernel's (floor0.LINE, read through `line_state`). `NEXT`
gives, for every state the automaton can be in, the one role that moves it and how. The table is checked against LINE
for exhaustiveness (tests/test_m2_review.py), so a new state in the TCB is a failing test here, not a silent stall.

Pure functions of the journal state: no I/O, no clock other than the time passed in."""
from __future__ import annotations

from dataclasses import dataclass

from tcb.floor0 import LINE, line_state

# line state -> (role, verb). None: the subject has no intent yet.
NEXT = {
    None: ("agent", "ask"),             # once the scanner's facts about this commit satisfy a condition of the law
    "intended": ("guard", "issue"),
    "tokened": ("guard", "redeem"),
    "reserved": (None, "wait"),         # a guard is sending it; only the dispatch window ends this
    "expired": ("scanner", "reconcile"),
    "uncertain": ("scanner", "reconcile"),
    "proving": ("scanner", "prove"),
    "failed": ("agent", "ask"),         # GitHub merged nothing: ask again on facts observed after the failure
}
STATES = {None, "expired"} | {to for _, to in LINE.values()} | {s for frm, _ in LINE.values() for s in frm}
OPEN = "open"                           # the scanner's `state` of a declared pull request that may still be merged


@dataclass(frozen=True)
class Subject:
    resource: str                       # repo:{area}:{item}/pr/{pr}/{head}
    area: str
    item: str
    pr: str
    head: str

    @property
    def args(self) -> dict:
        return {"area": self.area, "item": self.item, "pr": self.pr, "head": self.head, "method": "squash"}


@dataclass(frozen=True)
class Action:
    role: str
    verb: str
    subject: Subject
    intent: str | None = None
    condition: str | None = None


def subject_of(resource: str) -> Subject | None:
    base, sep, rest = resource.partition("/pr/")
    parts, tail = base.split(":"), rest.split("/")
    if not sep or len(parts) != 3 or parts[0] != "repo" or len(tail) != 2:
        return None
    return Subject(resource, parts[1], parts[2], tail[0], tail[1])


def declared(s, agent="agent") -> list:
    """Subjects exist only by the agent's signed declaration; nothing GitHub lists can add one."""
    out = []
    for o in s["observations"].values():
        if o["author"] == agent and o["property"] == "proposed" and o["status"] == "open":
            subject = subject_of(o["resource"])
            if subject:
                out.append(subject)
    return sorted(out, key=lambda x: x.resource)


def facts(s, subject: Subject, scanner="scanner", humans=()) -> dict:
    """property -> (status, at) from the independent sources about this exact commit."""
    out = {}
    for o in s["observations"].values():
        if o["resource"] == subject.resource and (o["author"] == scanner or o["author"] in humans):
            if o["property"] not in out or o["at"] > out[o["property"]][1]:
                out[o["property"]] = (o["status"], o["at"])
    return out


def latest_intent(s, subject: Subject):
    found = [it for it in s["intents"].values()
             if it["op"] == "remediate" and it["resource"] == subject.resource]
    return max(found, key=lambda it: it["stmt"]["at"]) if found else None


def condition(f: dict, since: int) -> str | None:
    """Which condition of the law the facts satisfy. CI, scope and review are properties of the commit itself; only
    whether the pull request is still open at this head can change, so after a failure (`since`) that one fact must
    have been observed again."""
    status = {k: v for k, (v, _) in f.items()}
    if status.get("ci") != "green" or status.get("state") != OPEN or f["state"][1] <= since:
        return None
    if status.get("scope") == "dependencies":
        return "remediate-autonomous"
    if status.get("review") == "approved":
        return "remediate-reviewed"
    return None


def plan(s, now: int, humans=()) -> list:
    """Every action due now, for every declared subject."""
    actions = []
    for subject in declared(s):
        it = latest_intent(s, subject)
        state = line_state(s["line"], it["id"], now) if it else None
        role, verb = NEXT[state]
        if state == "proving" and f"proof:{it['id']}" not in s["obligations"]:
            continue                                                # proven: nothing left for this subject
        if verb == "ask":
            f = facts(s, subject, humans=humans)
            if f.get("state", (OPEN,))[0] != OPEN:
                continue                                            # merged, closed or moved: nothing left to ask
            since = it["stmt"]["at"] if it else -1
            cond = condition(f, since)
            actions.append(Action("scanner", "observe", subject))   # facts are refreshed while nothing is asked
            if cond:
                actions.append(Action(role, verb, subject, it["id"] if it else None, cond))
        elif role:
            actions.append(Action(role, verb, subject, it["id"]))
    return actions
