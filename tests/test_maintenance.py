"""Planning must not confuse work, historical health and permission."""
from fixture import World, run, copy
from maintenance import plan


def health():
    return {"state": "IN_PROGRESS", "head": "sha256:example", "size": 1,
            "as_of": 100, "evaluated_at": 100, "open": [
                {"obligation": "target:ci", "type": "target", "owner": "alice", "due": 200,
                 "needs": ["repair", "observe"], "target": "ci"}], "escalated": []}


def test_work_does_not_mutate_audit_or_confer_permission():
    view = health()
    before = copy.deepcopy(view)
    result = plan(view)
    assert result["status"] == "WORK" and result["read_only"]
    assert result["work"][0]["steps"] == ["observe", "repair"]
    result["work"][0]["needs"].clear()
    assert view == before
    assert "token" not in result and "capability" not in result


def test_fault_and_historical_audits_produce_no_agent_work():
    for view in ({"state": "FAULT"}, {**health(), "current": False}):
        result = plan(view)
        assert result["status"] == "BLOCKED" and not result["work"]


def test_escalated_work_remains_a_human_decision():
    view = health()
    view.update(state="ESCALATED", escalated=view["open"], open=[])
    result = plan(view)
    assert result["status"] == "REVIEW" and not result["work"]
    assert result["human"][0]["next"] == "human_review"


def test_uncertain_protocol_effects_do_not_become_repair_requests():
    view = health()
    view["open"][0].update(type="protocol", stage="reconcile")
    result = plan(view)
    assert result["status"] == "REVIEW" and not result["work"]


def test_inconsistent_and_duplicate_obligations_block_projection():
    view = health()
    for bad in ({**view, "state": "PROVEN"}, {**view, "open": view["open"] * 2},
                {**view, "head": None}, {**view, "state": "ESCALATED"},
                {**view, "open": []}, {**view, "evaluated_at": 99}):
        assert plan(bad)["status"] == "BLOCKED"


def test_real_audit_becomes_work_without_a_journal_write():
    w = World()
    try:
        before = w.state["head"]
        verdict = w.journal.health()
        result = plan(verdict)
        assert result["status"] == "REVIEW", (verdict, result)
        assert result["human"][0]["obligation"] == "clock:witness"
        from tcb.floors import FLOORS
        assert {ob["target"] for ob in result["work"]} == {t["id"] for t in FLOORS["targets"]} | {"pr42-ci"}
        assert result["basis"]["head"] == before == w.state["head"]
    finally:
        w.journal.close()


if __name__ == "__main__":
    run(globals())
