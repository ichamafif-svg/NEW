"""FLOOR-0: what guards the law itself. Applied by the kernel; the sealed law only declares it, and must declare exactly
this text, this polarity table and these constants (one digest covers all three)."""
from .canon import digest

FLOOR0 = (
    ("F0-1", "No single actor: human quorum k >= MIN_HUMANS, at least k+2 humans, and enough witnesses. "
             "Recovery remains conditional on their response."),
    ("F0-2", "For every critical property, name its controls, common dependencies and covered failures. "
             "A safety disagreement blocks the effect; an integrity mismatch blocks the affected boundary. "
             "A local stop is not an unsigned ledger mutation."),
    ("F0-3", "Code and floors are genesis-bound. The client law changes only by quorum, witnessed delay and activation, "
             "never weakening the release floors; capability chains only narrow. A law constrains only kinds that act, "
             "attest or attenuate: never a restriction, a witness or the widening protocol."),
    ("F0-4", "Every canonical state transition is caused by exactly one signed entry. Admission depends only on "
             "the admitted prefix and the pinned law and code."),
    ("F0-5", "Every kind has one polarity. Genesis establishes the initial externally pinned root by quorum. Later widening needs a human quorum, an attested delay, then explicit quorum "
             "activation. Other polarities only restrict, attenuate, act under capability, attest or witness."),
    ("F0-6", "Time only expires or lapses authority; it never grants it. Only witness quorum advances the attested "
             "anchor; ordinary entry timestamps are monotone and bounded ahead of that anchor. A restriction may share "
             "the last instant, so no timestamp can starve it."),
    ("F0-7", "Lifting a unilateral restriction is a widening. k+1 humans may override a veto after its delay."),
    ("F0-8", "A fact permits an action only while freshly attested by a chain sharing no holder with the actor. "
             "Every permitting fact carries its provenance label: observations, closures, open instances and gates. "
             "Absence of a fact never permits it."),
    ("F0-9", "Every effect is typed, its resource derives from its arguments, and its reservation is durable and "
             "single-use. Rejudging and provider dispatch are ordered against admission. Only the judged canonical "
             "request is passed to the trusted adapter, with a genesis-bound reservation key. The effect line follows "
             "one table; a reservation leaves within DISPATCH_MS or never, and only then may it be reconciled."),
    ("F0-10", "History is append-only and genesis-bound. An independent monotone pin is retained for every write "
              "before acknowledgment. History below or diverging from it is blocked; repair restores its exact tail."),
    ("F0-11", "Outside admission, each declared target lacking fresh independent proof has a stable obligation "
              "and deadline; overdue gaps record escalation to root humans. Accountability never authorizes. "
              "Recording escalation does not prove delivery or repair."),
)

MIN_HUMANS = 2
MIN_WITNESSES = 2
MIN_DELAY_MS = 3_600_000          # a widening waits at least one hour of witnessed time
MAX_AHEAD_MS = 300_000            # no statement runs more than five minutes ahead of the last witnessed time

KINDS = ("human", "agent", "service", "oracle", "guard", "witness", "sentinel")

# One polarity per kernel kind. Law-declared evidence kinds are always "attest".
POLARITY = {
    "genesis": "widen", "rotate": "widen", "grant": "widen", "unfreeze": "widen", "law": "widen", "activate": "widen",
    "delegate": "attenuate",
    "veto": "restrict", "revoke": "restrict", "freeze": "restrict", "flag": "restrict", "heartbeat": "restrict",
    "checkpoint": "witness",
    "intent": "act", "token": "act", "reservation": "act", "execution": "act",
    "reconciliation": "attest", "observation": "attest",
}

# Who may restrict on their own. "revoke" is also open to any holder along the revoked chain.
RESTRICT_BY = {
    "veto": ("human",), "revoke": ("human",), "freeze": ("human", "sentinel"),
    "flag": ("human", "sentinel"), "heartbeat": ("sentinel",),
}

# The effect line: one automaton, read by both judges. (kind, result) -> (states it may leave, state it enters).
# "expired" is a reservation past DISPATCH_MS: no guard may send it any more, so only then may a reconciler settle it.
DISPATCH_MS = 300_000
LINE = {
    ("intent", None): ((None,), "intended"),
    ("token", None): (("intended",), "tokened"),
    ("reservation", None): (("tokened",), "reserved"),
    ("execution", "ok"): (("reserved", "expired"), "proving"),
    ("execution", "failed"): (("reserved", "expired"), "failed"),
    ("execution", "unknown"): (("reserved", "expired"), "uncertain"),
    ("reconciliation", "applied"): (("uncertain", "expired"), "proving"),
    ("reconciliation", "not_applied"): (("uncertain", "expired"), "failed"),
}


def line_state(line: dict, intent: str, at: int):
    """The state of an intent's effect line at `at` (None before the intent exists)."""
    cur = line.get(intent)
    if cur is None:
        return None
    return "expired" if cur["state"] == "reserved" and at > cur["at"] + DISPATCH_MS else cur["state"]


LAPSE = ("pending", "unredeemed")  # stages before any effect: time lapses them. After a reservation nothing lapses.


def floor0_digest() -> str:
    return digest({"text": [list(item) for item in FLOOR0], "polarity": POLARITY, "restrict_by": {k: list(v) for k, v in RESTRICT_BY.items()},
                   "constants": {"MIN_HUMANS": MIN_HUMANS, "MIN_WITNESSES": MIN_WITNESSES,
                                 "MIN_DELAY_MS": MIN_DELAY_MS, "MAX_AHEAD_MS": MAX_AHEAD_MS,
                                 "LAPSE": list(LAPSE), "KINDS": list(KINDS), "DISPATCH_MS": DISPATCH_MS},
                   "line": [[k, r, list(f), t] for (k, r), (f, t) in LINE.items()]})
