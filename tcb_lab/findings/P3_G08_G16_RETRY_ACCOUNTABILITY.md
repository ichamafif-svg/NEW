# IV-E — Discrimination dette / proposition / escalade

**9 octobre 2026.** Baseline verified: [run 37965039223](https://github.com/ichamafif-svg/NEW/actions/runs/37965039223), the initial IV-E pair. In eight cycles under `found:2` and failing `tests=found:1`, one proposal is withdrawn after cycle 2; `lifecycle.plan` is empty on cycles 2–8; main remains unchanged. Valid healthy control: no proposal, no plan. This is a behavioral observation, not a proved loss of constitutional debt.

## Mechanism read from ops source, to discriminate empirically

- `lifecycle.before_intent`: scanner tests other than `green` give `rejected` (then agent `withdraw`).
- `cycle.cmd_agent`: an agent consumes a withdraw action, **then** invokes `propose`; not having a live subject does not by itself imply an automatic new proposal.
- `cycle.propose`: a failed build records a signed `attempt:failed` for the logical target and imposes `ATTEMPT_BACKOFF_MS = DAY` on retries. Since Sim cycles are one minute, eight cycles cannot distinguish an intentional 24h backoff from an indefinitely abandoned target. This is **a competing explanation**, not a verified classification of those traces.
- `lifecycle.plan` only schedules actions on declared **transition subjects**; the continuing **floor target** and the **constitutional obligation** are separate identities.

## New IV-E discriminating instrument

The IV-E experiment has been extended to capture, per cycle, three previously missing observations: `node.journal.health(required_at=now)` counts for `open / escalated / proven`, signed `attempt` facts including timestamps, and declared lifecycle plans. This distinguishes an empty transition plan from an untracked accountability target, and gives testable provenance for backoff. **New instrument run pending**; the old IV-E result does not contain these columns.

## What will settle G08 / G16

**G08:** state whether the floor/requirement gap remains `open` even after the repair proposal is withdrawn, including its stable clock and canonical subject. Do not infer an obligation's nonexistence from the absence of an `effect proof` debt.

**G16:** contrast minute-scale retry/backoff with a run advancing past `ATTEMPT_BACKOFF_MS` (while maintaining valid witness/freshness assumptions); distinguish an authorized alternative repair, bounded escalation, and genuinely silent stall. Record the escalation record, not just its count, and test permitted-progress positive controls.

**No scope or runtime code change.** Claims in the first observation are preserved and not silently reinterpreted.
