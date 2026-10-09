# DEEP_ASSESSMENT — Hybrid Standard production candidate

**Status: IMPLEMENTATION_IN_PROGRESS / PRODUCTION_BLOCKED.** This is an adversarial architecture and code assessment, not an independent formal audit. Target branch: `prototype/hybrid-kernel-v1`. Legacy `tcb/` is the **non-regression reference**, not a library that may silently weaken constitutional floors. The new Standard is the eventual unified runtime, not an agent orchestration engine disguised as a kernel.

## A. Verified by reading source — what exists

- `tcb/kernel.py`: deterministic admission and delta, signed entry requirements, capability chains, polarity, quorum, delays, veto/restriction, intent/token/reservation/execution/reconciliation, proof controls, witnessed time. This provides deeper constitutional coverage than `hybrid_kernel/core.py`.
- `tcb/law.py` / `tcb/floor0.py` / `tcb/floors.py`: release floors and client-law composition. These are constitutional semantics to preserve.
- `tcb/ledger.py` + `tcb/pins.py`: independent pin-store *contract*, replay, transaction and recovery. Separate filenames alone **do not** ensure independent rollback domains.
- `tcb/invariants.py`: secondary checks of critical transitions. Does **not** independently reimplement every law or prove genuine process/runtime independence.
- `tcb/guard.py` / `tcb/effects.py`: reserve/rejudge/send/report; physical egress and credential monopoly remain deployment properties.
- `tcb/accountability.py`: deterministic compliance debt based on targets with expiry/escalation. This silo does not automatically authorize K effects; do not collapse `health.open` into `state["obligations"]`.
- `hybrid_kernel/core.py`: pure proposed generic relationship-inspired policy/delta/debt path, **not** a replacement for full authority. Its `context.allowed` is unacceptable as a privileged source of law.
- `hybrid_kernel/runtime.py`: signed entries routed to the inherited full kernel, journal, second checker and effect guard. **This is the current constitutional reference route; there must not be a competing privileged judge.**
- `hybrid_kernel/externals.py`: nine contract types and operator-controlled inventory, with failures closed on missing/unverified/expired entries; these are a **skeleton**, not deployed trust assurances.
- `hybrid_kernel/deployment.py`: operator provisioning gate. A boolean asserting physical enforcement is **not cryptographic attestation**; MUST NOT be exposed to agents, client requests or untrusted HTTP.

## B. Blocking defects / architectural debts (P0)

**P0.1 — Two model generations.** A generic hybrid model and legacy fixed statement kinds coexist. Production authority remains with legacy. **To finish**, the new model must completely preserve quorum/restriction/attenuation/witness/effect properties before the legacy entrypoint can be retired; a 'wrapper' alone is not the completed hybrid kernel.

**P0.2 — Unverified physical trust.** Real root-key custody, independent humans, trusted runtime pin, rollback domain, witness clock, independent checker and provider exclusive egress cannot be inferred from successful local tests or operator-supplied strings. A deployment that lacks any required trust domain must refuse privileged action.

**P0.3 — Exact effect model.** Need production-enforced full destination and payload bytes, channel isolation, dispatch-time authority recheck, idempotency/reservation and readback under uncertainty. A `Decision.authorization` structure from the experimental core cannot be used as a capability for live cloud mutations.

**P0.4 — External-proof semantics.** DSSE signature authenticates provenance, not truth, coverage or independence. Evidence may close obligations or release privileges only under a separately assessed verifier/attestor with exact subject and method binding.

**P0.5 — Robustness and non-regression.** Old code provides historical properties, not automatic VNext equivalence. Need signed-state transition corpus, differential verification, fuzzing of all entry kinds, recovery/fork/rollback fault injection and stable artifact evidence. GitHub workflows created so far are not sufficient by themselves.

## C. Secondary technical debt (P1)

- Stable semantic object identity independent of business aliases; migration/rename without resetting `opened`/`due`.
- Versioned extensibility of typed entity/relation graph without arbitrary code execution in the constitutional DSL.
- Explicit `UNKNOWN` provider state and reconciliation when timeout races revocation.
- Compliance/debt escalation state without importing a scheduler or a product workflow engine into K.
- SLO and observability for **trusted boundary operations** separately from BUILD/RUN monitoring.

## D. Concrete integration gates and one-way convergence

1. Keep exactly **one privileged admission source**: `ConstitutionalRuntime.admit` calling `tcb.Kernel` inside `Journal` until a structurally stronger replacement has been adversarially demonstrated. `hybrid_kernel.core.judge` remains a **non-privileged reference candidate**, not a production oracle.
2. All release-critical code must trace to G01–G16 and T01–T09, and produce passing evidence in `release_readiness.json` under external review. Test green is not authority to self-set a `verified` flag.
3. Finish typed constitutional model and a representation-independent judgment adapter. Migrate **one semantic mechanism at a time**, run same signed cases through legacy and new path and reject accidental power widening. Do not force hard business maps.
4. Isolate trusted effects via a genuinely guarded deployment; provider credentials must not exist in agents. Require proofs of exclusion of alternate deployment routes.
5. Validate physical assumptions on the actual runtime, including multiple independent restoration domains and principal separation.
6. Enforce promotion through an independent reviewer and an explicit release/genesis transition. An uncontrolled merge is not a constitutional upgrade.

## E. Delivery contract

A complete production **implementation** consists of a unified generic constitutional judgment engine, lossless migration or new signed genesis, all legal transitions, valid proof/debt/effect machinery, trusted-external ports with at least one validated implementation of each mandatory physical contract, attack tests and a release manifest grounded in independent evidence. 

**Current reality:** baseline source is substantially functional; new generic hybrid engine is only partially implemented; real Trusted Externals are mostly specified rather than proven; production release is therefore **BLOCKED**. The work is substantial and cannot honestly be closed by adding declarations or tests that were never run.

## F. Updated artifacts

- [Conceptual model](KERNEL_CONCEPTUAL_MODEL.md)
- [Trusted External contracts](TRUSTED_EXTERNAL_CONTRACTS.md)
- [Execution protocol](KERNEL_EXECUTION_PROTOCOL.md)
- [Reuse matrix](PRODUCTION_GAP_AND_REUSE.md)
- [Release readiness manifest](release_readiness.json)
- [Release gate](release_gate.py)

**No files in `tcb/`, `ops/` or the frozen laboratory were modified by this assessment.**
