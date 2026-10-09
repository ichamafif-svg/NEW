# Phase 3 — Campaign II: empirical contradiction register

**Primary evidence:** [GitHub Actions run 37953933593](https://github.com/ichamafif-svg/NEW/actions/runs/37953933593), adversarial job `113899507394`, executed at the same commit for the 16 O1 repeats. Local CI fixture with fresh temp git repos/keys on each repetition; neither equivalent initial bytes nor deterministic scheduling has been established.

## O1 — observed divergence on repeated historic red case

`p3_depth_autonomy.py`: ten replays of `Sim({"vulns":"found:2"})`, with `default_test="found:1"`, two cycles each. The logs show multiple `historic_assertions_hold: false` **and** `true` within the *same workflow run*. At least one failing repetition ends with subjects `["measuring","withdrawn"]`, `live=true`, while another ends with `["withdrawn"]`, `live=false`.

**Scientific implication:** previous claim that the historical red cannot be reproduced was too strong. It **has now been observed again inside a fixed-source test run**, but the fixture generates a fresh git commit/key set each time; therefore this is **not yet proof of nondeterminism for byte-identical state and input**. A possible mechanism is a new subject generated while the first was withdrawn, or an order / branch-address sensitive observation. A bug in expectations or simulation remains a competing hypothesis.

**Required next depth:** preserve all parent child subject identities, pre/post state, deterministically pin the fixture's initial conditions and timestamps, repeat against the same fixture snapshot, separate (a) original withdrawn from (b) new live subject, trace obligations and progress. Do **not** patch lifecycle to force a desired verdict.

## E1 — eight additional same/different-journal contrasts

`p3_depth_effect.py` ran eight local variations crossing response `ack_lost|unknown|ok|failed` and same guard versus another journal sharing SQLite. Logs show second redemption rejected with `HIST.TIME` in all eight cases. **This observation alone does not establish a distributed fencing invariant:** `HIST.TIME` may precede the guard/idempotence check; the test must vary the timestamp relative to fresh witnessed time and separately probe multiple hosts.

## P1 — seven additional signed-proof contrasts

`p3_depth_proof.py` ran `true_exact`, `false_exact`, `wrong_subject`, `false_oracle_actor`, `claimed_lower_grade`, `claimed_higher_grade`, `future_timestamp`. The false/true label is **external to the signed entry**, meaning the tests isolate what a signature can authenticate, not whether the proof oracle actually measured reality. Further experiments need provenance, coverage, stale-but-plausible time, conflict resolution, and independent external observation.

## Reporting correction

Previously `ci_report.py` counted only explicit `INCONCLUSIVE` and `VIOLATION_OBSERVED`; a measured `OBSERVED` row with `historic_assertions_hold=false` appeared as zero flagged. The reporting code now marks this as **historical mismatch**, while leaving exploratory suites free to record contradictions rather than failing prematurely. Validate on next CI run before treating its issue summary as authoritative.

## Next scientific questions

1. O1: Under precisely which initial state does a new `measuring` subject coexist with the withdrawn one, and is that desirable governed progress or an error? Analyze identity of the two subjects, not just count.
2. E1: Does the same guard refuse a second departure with fresh valid time and pre-existing reservation, including simulated crash or response delayed? Can another process use a physically distinct credential?
3. P1: Which claims are checked as facts, and which are assertions of trust in the oracle? What is the contract between raw observation, evidence signer, and independent proof?
4. All: separate failures in test harness, logic and physical trust boundaries. Never promote any of these observations directly to an architectural choice.

**Phase 3 continues; scope and kernel untouched.**
