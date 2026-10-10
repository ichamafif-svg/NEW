"""Reserve durably, rejudge under the journal write gate, dispatch once, report."""
import copy
import uuid

from .canon import canon, digest
from .effects import EffectPort, NotDispatched
from .kernel import Refused
from .invariants import Disagreement
from .ledger import entry
from .release import code_digest
from .sign import envelope


class Guard:
    def __init__(self, journal, identity, signer, effect_port, validity_check=None):
        if journal.genesis_pin is None or journal.pin_store is None:
            raise ValueError("guard requires external genesis and live durable pins")
        if not isinstance(effect_port, EffectPort):
            raise ValueError("an explicit trusted EffectPort is required")
        journal.pin_store.bind(journal.genesis_pin)
        if journal.kernel.code_pin != code_digest():
            raise ValueError("code release changed")
        self.journal, self.identity, self.signer = journal, identity, signer
        self.effect_port = effect_port
        self.validity_check = validity_check

    def _valid_at(self, at):
        if self.validity_check is None:
            return at
        now = self.validity_check()
        if type(at) is not int or at < now:
            raise Refused("TRUST.TIME", "the supplied time precedes trusted time")
        return now

    def _entry(self, state, kind, body, cosigners=()):
        env = envelope(state["domain"], kind, {"author": self.identity, **body}, [self.signer, *cosigners])
        return entry(state["size"], state["head"], env)

    def issue(self, intent_id, at, cosigners=()):
        self._valid_at(at)
        def build(state):
            self._valid_at(at)
            it = state["intents"].get(intent_id)
            if it is None:
                raise Refused("GUARD.UNKNOWN", "the intent is not in this journal")
            return self._entry(state, "token", {"id": f"tok-{uuid.uuid4().hex}", "at": at, "intent": intent_id,
                                                "args_digest": digest(copy.deepcopy(it["args"]))}, cosigners)
        return self.journal.transact(build)[0]

    def redeem(self, token_id, at):
        self._valid_at(at)
        def reserve(state):
            self._valid_at(at)
            tok = state["tokens"].get(token_id)
            if tok is None or tok["guard"] != self.identity:
                raise Refused("GUARD.UNKNOWN", "not a token of this guard")
            return self._entry(state, "reservation", {"id": f"res-{uuid.uuid4().hex}", "at": at, "token": token_id})
        self.journal.transact(reserve)
        # The write gate covers reauthorization and the actual adapter send, never the deferred wait.
        try:
            with self.journal.effect_gate() as state:
                trusted_at = self._valid_at(at)
                if state["code"] != code_digest():
                    raise ValueError("code release changed")
                when = max(at, trusted_at, state["last_at"])
                it = self.journal.kernel.judge_dispatch(state, token_id, self.identity, when)
                try:
                    checked = self.journal.invariants.dispatch(state, token_id, when, self.journal.kernel.law_of(state))
                except Exception as exc:
                    self.journal._halt("dispatch check failed: " + str(exc))
                judged = {"op": it["op"], "resource": it["resource"], "args": copy.deepcopy(it["args"])}
                if canon(judged) != canon(checked):
                    self.journal._halt("the two judges produced different physical effects")
                reservation_key = digest({"genesis": state["domain"], "reservation": state["reserved"][token_id]})
                result = self.effect_port.perform(judged, canon(judged), reservation_key)
        except (Refused, NotDispatched):
            result = "failed"                  # refused before departure: nothing was sent
        if callable(result):
            try:
                result = result()              # only awaits an already-sent request; adapters remain trusted
            except Exception:
                result = "unknown"
        result = result if result in ("ok", "failed", "unknown") else "unknown"
        def report(state):
            return self._entry(state, "execution", {"id": f"exe-{uuid.uuid4().hex}",
                                                    "at": max(at + 1, state["last_at"] + 1),
                                                    "token": token_id, "result": result})
        return self.journal.transact(report)[0]
