"""Adversarial checks of the kernel's concepts: polarity, time, root, exits, typed effects, independent facts."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixture import DAY, H, MIN, T0, Kernel, Refused, World, copy, digest, identity, make_law, raises, run  # noqa: E402
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey  # noqa: E402


# ---- F0-1: the root ---------------------------------------------------------------------------------------------
def test_root_needs_a_human_beyond_the_quorum():
    w = World(genesis=False)
    for ids in (["alice", "bob", "carol"], ["alice", "bob"], ["alice"]):
        root = {"threshold": 2, "identities": {n: w.root["identities"][n] for n in ids + ["agent", "w1", "w2"]}}
        w.refuse("FLOOR0.ROOT", "genesis", "alice", T0, ["alice", "bob"][:len(ids)], root=root, law=w.law)
    bad = copy.deepcopy(w.root)
    bad["identities"]["alice"] = {"kind": "human", "keys": "not-a-list"}
    w.refuse("TYPE.ROOT", "genesis", "bob", T0, ["bob", "carol"], root=bad, law=w.law)


# ---- F0-5 / F0-6: widening is explicit; time never grants --------------------------------------------------------
def test_a_proposal_never_activates_by_itself():
    w = World()
    root = copy.deepcopy(w.root)
    del root["identities"]["sentinel"]
    pid = w.add("rotate", "alice", T0 + 1, ["alice", "bob"], root=root)
    w.tick(T0 + 10 * DAY)
    w.add("heartbeat", "sentinel", T0 + 10 * DAY + 1, seen=0)     # time passed: nothing changed
    assert "sentinel" in w.state["root"]["identities"] and pid in w.state["proposals"]
    w.refuse("FLOOR0.QUORUM", "activate", "alice", T0 + 10 * DAY + 2, ["alice"], proposal=pid)
    w.add("activate", "alice", T0 + 10 * DAY + 3, ["alice", "carol"], proposal=pid)
    assert "sentinel" not in w.state["root"]["identities"]


def test_activation_waits_for_witnessed_delay():
    w = World()
    pid = w.add("grant", "alice", T0 + 1, ["alice", "bob"], holder="agent", actions=["effect:merge"],
                resources=["repo:pr:*"], conditions=[], not_after=T0 + 30 * DAY)
    w.refuse("WIDEN.DELAY", "activate", "alice", T0 + 2, ["alice", "bob"], proposal=pid)
    w.refuse("HIST.AHEAD", "activate", "alice", T0 + H + 1, ["alice", "bob"], proposal=pid)   # no witness yet
    w.tick(T0 + H + 1)
    w.add("activate", "alice", T0 + H + 2, ["alice", "bob"], proposal=pid)
    assert pid in w.state["grants"]


def test_a_single_witness_cannot_move_time():
    w = World()
    s = w.state
    w.refuse("FLOOR0.WITNESS", "checkpoint", "w1", T0 + 10 * DAY, ["w1"], size=s["size"], head=s["head"])
    w.refuse("CAP.WITNESS", "checkpoint", "alice", T0 + 10 * DAY, ["alice", "w1", "w2"], size=s["size"], head=s["head"])
    from tcb.law import LawError
    weak = make_law(witnesses={"quorum": 1})
    with raises(LawError, "only tighten"):
        Kernel().load(weak)


def test_activation_cannot_borrow_the_ahead_window():
    w = World()
    pid = w.add("grant", "alice", T0 + 1, ["alice", "bob"], holder="agent", actions=["effect:merge"],
                resources=["repo:pr:*"], conditions=[], not_after=T0 + DAY)
    due = T0 + H + 1
    w.tick(due - 1)
    w.refuse("WIDEN.DELAY", "activate", "alice", due, ["alice", "bob"], proposal=pid)


def test_root_cannot_remove_the_time_quorum():
    w = World()
    weak = copy.deepcopy(w.root)
    del weak["identities"]["w2"]
    w.refuse("FLOOR0.WITNESS", "rotate", "alice", T0 + 1, ["alice", "bob"], root=weak)
    first = World(genesis=False)
    weak = copy.deepcopy(first.root)
    del weak["identities"]["w2"]
    first.refuse("FLOOR0.WITNESS", "genesis", "alice", T0, ["alice", "bob"], root=weak, law=first.law)


def test_rotated_key_is_dead_from_the_activation_entry_on():
    w = World()
    old = {"alice": w.keys["alice"]}
    new_key = Ed25519PrivateKey.generate()
    root = copy.deepcopy(w.root)
    root["identities"]["alice"] = identity("human", new_key)
    _, t = w.widen("rotate", T0 + 1, signers=("bob", "carol"), root=root)
    w.refuse("SIG.INVALID", "freeze", "alice", t, keys=old, scope="*")
    w.keys["alice"] = new_key
    w.add("freeze", "alice", t + 1, scope="*")


def test_a_proposal_from_an_older_root_is_stale():
    w = World()
    root = copy.deepcopy(w.root)
    pid = w.add("grant", "alice", T0 + 1, ["alice", "bob"], holder="agent", actions=["effect:merge"],
                resources=["repo:pr:*"], conditions=[], not_after=T0 + 30 * DAY)
    root["identities"]["w3"] = identity("witness", Ed25519PrivateKey.generate())
    _, t = w.widen("rotate", T0 + 2, root=root)
    w.refuse("WIDEN.STALE", "activate", "alice", t, ["alice", "bob"], proposal=pid)
    w.refuse("WIDEN.UNKNOWN", "activate", "alice", t + 1, ["alice", "bob"], proposal="nothing")


# ---- F0-7: exits for unilateral restrictions --------------------------------------------------------------------
def test_veto_and_its_exit_by_a_higher_quorum():
    w = World()
    root = copy.deepcopy(w.root)
    del root["identities"]["carol"]["keys"][0]
    root["identities"]["carol"] = identity("human", Ed25519PrivateKey.generate())   # alice and bob replace carol's key
    pid = w.add("rotate", "alice", T0 + 1, ["alice", "bob"], root=root)
    w.refuse("CAP.VETO", "veto", "bob", T0 + 2, proposal=pid)         # a signer cannot veto
    w.add("veto", "carol", T0 + 3, proposal=pid)
    assert pid not in w.state["proposals"]
    # carol could stall a quorum of 2 forever: the exit is an override by k+1 humans, with a doubled delay
    w.refuse("FLOOR0.QUORUM", "rotate", "alice", T0 + 4, ["alice", "bob"], root=root, override=True)
    w.refuse("FLOOR0.QUORUM", "rotate", "alice", T0 + 5, ["alice", "bob", "sentinel"], root=root, override=True)


def test_override_with_k_plus_one_humans():
    roles = {**__import__("fixture").ROLES, "dave": "human"}
    w = World(roles=roles)
    root = copy.deepcopy(w.root)
    del root["identities"]["carol"]
    root["identities"]["eve"] = identity("human", Ed25519PrivateKey.generate())
    pid = w.add("rotate", "alice", T0 + 1, ["alice", "bob", "dave"], root=root, override=True)
    w.refuse("CAP.VETO", "veto", "carol", T0 + 2, proposal=pid)
    w.tick(T0 + H)
    w.refuse("WIDEN.DELAY", "activate", "alice", T0 + H + 1, ["alice", "bob"], proposal=pid)
    w.tick(T0 + 2 * H + 1)
    w.add("activate", "alice", T0 + 2 * H + 2, ["alice", "bob"], proposal=pid)
    assert "carol" not in w.state["root"]["identities"]


def test_lifting_a_freeze_is_a_widening():
    w = World()
    w.add("freeze", "sentinel", T0 + 1, scope="repo:prod:*")
    w.refuse("FLOOR0.QUORUM", "unfreeze", "carol", T0 + 2, scope="repo:prod:*")
    pid = w.add("unfreeze", "alice", T0 + 3, ["alice", "bob"], scope="repo:prod:*")
    w.add("freeze", "sentinel", T0 + 4, scope="repo:prod:*")         # frozen again after the proposal
    w.tick(T0 + H + 3)
    w.refuse("WIDEN.STALE", "activate", "alice", T0 + H + 4, ["alice", "bob"], proposal=pid)
    _, t = w.widen("unfreeze", T0 + H + 5, scope="repo:prod:*")
    assert w.state["frozen"] == {}


# ---- capabilities and patterns ----------------------------------------------------------------------------------
def test_patterns_end_on_a_separator():
    w = World()
    w.refuse("TYPE.SHAPE", "grant", "alice", T0 + 1, ["alice", "bob"], holder="agent", actions=["effect:merge"],
             resources=["repo:pr*"], conditions=[], not_after=T0 + DAY)
    gid, t = w.grant("agent", ["effect:merge"], ["repo:pr:*"], T0 + 2)
    w.refuse("CAP.WIDENS", "delegate", "agent", t, parent=gid, holder="agent", actions=["effect:merge"],
             resources=["repo:*"], conditions=[], not_after=T0 + DAY)
    w.add("delegate", "agent", t + 1, parent=gid, holder="agent", actions=["effect:merge"],
          resources=["repo:pr:7"], conditions=[], not_after=T0 + DAY)


def test_removed_holder_loses_every_chain():
    w = World()
    gid, t = w.grant("agent", ["effect:merge"], ["repo:pr:*"], T0 + 1)
    child = w.add("delegate", "agent", t, parent=gid, holder="ci", actions=["effect:merge"], resources=["repo:pr:7"],
                  conditions=[], not_after=T0 + 20 * DAY)
    root = copy.deepcopy(w.root)
    del root["identities"]["agent"]
    _, t = w.widen("rotate", t + 1, root=root)
    w.refuse("CAP.WITHDRAWN", "intent", "ci", t, under=child, op="merge", args={"pr": "7", "method": "squash"})


# ---- F0-9: typed effects ------------------------------------------------------------------------------------------
def test_effect_arguments_are_closed_and_derive_the_resource():
    w = World()
    gid, t = w.grant("agent", ["effect:merge"], ["repo:pr:7"], T0 + 1)
    ok = {"pr": "7", "method": "squash"}
    for args, why in (({"pr": "7"}, "missing"), ({**ok, "force": True}, "undeclared"), ({"pr": ["7"], "method": "x"}, "list"),
                      ({"pr": "7:../8", "method": "x"}, "separator")):
        w.refuse("TYPE.ARGS", "intent", "agent", t, under=gid, op="merge", args=args)
    w.refuse("CAP.SCOPE", "intent", "agent", t, under=gid, op="merge", args={"pr": "8", "method": "squash"})
    w.refuse("TYPE.SHAPE", "intent", "agent", t, under=gid, op="merge", args=ok, resource="repo:pr:7")
    w.refuse("TYPE.OP", "intent", "agent", t, under=gid, op="delete", args=ok)
    iid = w.add("intent", "agent", t, under=gid, op="merge", args=ok)
    assert w.state["intents"][iid]["resource"] == "repo:pr:7"


# ---- F0-8: facts that widen ---------------------------------------------------------------------------------------
def test_negation_is_not_part_of_the_law():
    neg = [{"head": ["ok", []], "body": [["resource", ["?R"]], ["not", "stmt", ["args.branch", "main"]]]}]
    law = make_law(conditions={"not-main": neg})
    with raises(Exception, "condition"):
        Kernel().load(law)
    w = World()
    w.refuse("LAW.CONDITION", "grant", "alice", T0 + 1, ["alice", "bob"], holder="agent", actions=["effect:merge"],
             resources=["repo:pr:*"], conditions=[{"rules": neg}], not_after=T0 + DAY)


def test_conditions_read_only_independent_fresh_observations():
    w = World()
    gid, t = w.grant("agent", ["effect:merge"], ["repo:pr:*"], T0 + 1, conditions=["bot-author"])
    oid, t = w.grant("agent", ["observe", "certify:real"], ["repo:pr:*"], t)
    rid, t = w.grant("readback", ["observe", "certify:real"], ["repo:pr:*"], t)
    args = {"pr": "7", "method": "squash"}
    w.refuse("LAW.CONDITION", "intent", "agent", t, under=gid, op="merge", args=args)
    # the agent attests its own fact: ignored, it is the actor's chain
    w.add("observation", "agent", t + 1, under=oid, resource="repo:pr:7", property="pr_author",
          status="dependabot[bot]", level="real")
    w.refuse("LAW.CONDITION", "intent", "agent", t + 2, under=gid, op="merge", args=args)
    w.add("observation", "readback", t + 3, under=rid, resource="repo:pr:7", property="pr_author",
          status="dependabot[bot]", level="real")
    w.add("intent", "agent", t + 4, under=gid, op="merge", args=args)
    w.tick(t + 3 + DAY + 1)                                          # the fact goes stale: time only restricts
    w.refuse("LAW.CONDITION", "intent", "agent", t + 3 + DAY + 2, under=gid, op="merge", args=args)


if __name__ == "__main__":
    run(globals())
