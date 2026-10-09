# Campaign IV-B — Boundary closure dossier

**Status: UNDER REVIEW.** Scope remains fixed by [SCOPE.md](SCOPE.md), seven semantic responsibilities and three zones. This document reviews whether the **allocation** can be considered established; it does not change the scope, choose an abstraction, or confuse physical trust with optional untrusted tooling.

## Decision rules

A boundary can be **CLOSED_CONDITIONAL** if (1) the necessary information or physical capability is outside pure kernel computation, (2) the kernel-side check is exactly stated, (3) the external contract and counterfactual are explicit, and (4) falsifiers and residual deployment validation are listed. **CLOSED_CONDITIONAL is NOT a proven system guarantee**. **OPEN_CRITICAL** means no adequate external contract has been verified to make the promise enforceable. **OPEN_SEMANTIC** means the required pure semantics (e.g. obligation identity) are not yet specified/verified enough. `NOT_PROVEN` is never silently promoted.

## Decision by guarantee

| Guarantee | Boundary decision | Kernel obligation | Trusted external contract still required | What would falsify closure |
|---|---|---|---|---|
| G01 | CLOSED_CONDITIONAL | threshold and widening by distinct authorized logical signers | physical separation / key custody | one principal uses multiple independent-seeming identities |
| G02 | OPEN_CRITICAL | revocation, freeze, rejudgment at effect time | effect departure ordering across all privileged channels | outbound effect despite committed restriction |
| G03 | CLOSED_CONDITIONAL | monotone floors on change | authenticated runtime and release pin | effective weaker floor under alternate code |
| G04 | CLOSED_CONDITIONAL | full deterministic delta on signed prefix | exclusive durable state admission | two accepted divergent durable heads |
| G05 | OPEN_CRITICAL | verify domain-specific signed semantics | physical keys, identity binding, runtime | forged control or one human controls quorum |
| G06 | CLOSED_CONDITIONAL | expiration can restrict, never enlarge | truthful witnesses / departure clock | future time accepted as rights grant |
| G07 | OPEN_CRITICAL | prove eligibility, exact subject, coverage and independent method | actual truth/coverage/independence of source | false healthy evidence sufficient to authorize consequence |
| G08 | OPEN_SEMANTIC | preserve subject debt / due through renames/retries | durable facts and detection availability | new repair silently resets opening / debt |
| G09 | OPEN_CRITICAL | rejudge exact effect and conditions | no alternate egress and privileged effect fencing | bypass credentials effect without governed check |
| G10 | OPEN_CRITICAL | reserve and unknown state/reconciliation policy | durable provider idempotency/readback | duplicated physical effect after lost ACK |
| G11 | OPEN_CRITICAL | detect invalid history against anchor | independent antirollback anchor surviving restore | journal+pins reverted together without detection |
| G12 | OPEN_CRITICAL | fail closed on independent verifier disagreement | actually independent checker / input provenance | two matching checkers share false assumption |
| G13 | OPEN_CRITICAL | distinguish result status, qualified proof, target health | oracle truth and universe coverage | signed false healthy closes obligation |
| G14 | OPEN_CRITICAL | genesis / change / recovery authority floor | anchored installer, key custody and runtime | recovery actor installs effective god-mode |
| G15 | OPEN_CRITICAL | effect contract and governed entry paths | credential inventory, OS/provider network exclusivity | alternate writable token mutates target |
| G16 | OPEN_SEMANTIC | limits of autonomous work, debt and escalation rules | available scheduling/agents/scanners | no progress or hidden endless loop with allowed work |

**CLOSED_CONDITIONAL is a boundary allocation only.** These labels are research hypotheses supported by logical necessity and selective local observations, not empirical verification of all listed properties. A closed conditional contract must be revisited if deployment architecture changes an underlying assumption.

## Four next falsifier campaigns (blockers, not architecture)

**B1 Physical effects (G02/09/10/15):** 2 actual isolated processes and credential partitions; delayed provider ACK, restart at reservation/send boundary, concurrent guards, complete egress inventory. Record provider-side receipt count and exact bytes. If no physical test environment, label BLOCKED_EXTERNAL and state the tested provider contract required.

**B2 Same-subject debt/liveness (G08/16):** one requirement and target over 20/100 attempted repairs, withdrawals and identity changes, track original opened/due, latest verification and causes, control negative (still degraded) and positive (becomes healthy).

**B3 Truth/independence (G07/12/13):** alternative signer, shared physical data source, false method and incomplete universe; real signed payload variants, independent oracle readback, whether closure opens a subsequent effect.

**B4 Root/state trust (G01/03/04/05/06/11/14):** two physical key holders vs one key holder; forged witnessed time, pin ahead/behind and coordinated restore, code-pinning of runtime. Record where trust leaves K.

## Evidence requirements before declaring new freeze

For every G01–G16: signed input or trace, commit SHA, run, oracle and falsifier, accepted permitted control and rejected prohibited control, depth D0–D7, physical assumptions and external contract. Scope freeze can be **functionally delimited** before deployed validation, but security claims must remain qualified; **do not equate 'outside pure kernel' with 'outside effective TCB'.**

Current classification is published for review; **no declaration that all boundaries have been proven**.
