"""Turn a health view into work proposals. This is not a verifier or an authority.

Consumers must obtain health through the pinned auditor and rejudge every signed
intent. An obligation ID identifies work; it never constitutes permission.
"""
import copy


def plan(health):
    out = {"format": "standard-work-plan/1", "read_only": True,
           "status": "BLOCKED", "work": [], "human": []}
    try:
        if not isinstance(health, dict):
            raise ValueError("health must be an object")
        out["basis"] = {k: health.get(k) for k in ("head", "size", "as_of", "evaluated_at")}
        if health.get("state") == "FAULT" or health.get("current") is False:
            raise ValueError("audit unavailable or historical")
        if health.get("state") not in ("PROVEN", "IN_PROGRESS", "ESCALATED"):
            raise ValueError("unknown audit state")
        if (not isinstance(health.get("head"), str) or not health["head"]
                or type(health.get("size")) is not int or health["size"] < 1):
            raise ValueError("missing journal reference")
        for field in ("as_of", "evaluated_at"):
            if type(health.get(field)) is not int or health[field] < 0:
                raise ValueError("missing evaluation horizon")
        if health["evaluated_at"] < health["as_of"]:
            raise ValueError("evaluation horizon predates journal")
        seen = set()
        for field in ("open", "escalated"):
            rows = health.get(field)
            if not isinstance(rows, list):
                raise ValueError("missing obligation list")
            for ob in rows:
                if not isinstance(ob, dict):
                    raise ValueError("invalid obligation")
                ident = ob.get("obligation")
                if not isinstance(ident, str) or not ident or ident in seen:
                    raise ValueError("obligations must have unique stable identifiers")
                seen.add(ident)
                if type(ob.get("due")) is not int or ob["due"] < 0:
                    raise ValueError("missing deadline")
                item = copy.deepcopy(ob)
                if field == "escalated" or ob.get("type") != "target":
                    item["next"] = "human_review"
                    out["human"].append(item)
                else:
                    needs = ob.get("needs")
                    if (not isinstance(needs, list) or not needs
                            or any(n not in ("cover", "observe", "prove", "repair") for n in needs)):
                        raise ValueError("unknown maintenance need")
                    item["next"] = "propose_work"
                    item["steps"] = [n for n in ("cover", "observe", "repair", "prove") if n in needs]
                    out["work"].append(item)
        if health["state"] == "PROVEN" and seen:
            raise ValueError("proof verdict contradicts open obligations")
        if health["state"] == "IN_PROGRESS" and not seen:
            raise ValueError("progress verdict lacks obligations")
        if health["state"] == "ESCALATED" and not health["escalated"]:
            raise ValueError("escalation verdict lacks obligations")
        for field in ("work", "human"):
            out[field].sort(key=lambda ob: (ob["due"], ob["obligation"]))
        out["status"] = "REVIEW" if out["human"] else ("WORK" if out["work"] else "IDLE")
    except (ValueError, TypeError, KeyError) as exc:
        out.update(status="BLOCKED", work=[], human=[], reason=str(exc))
    return out
