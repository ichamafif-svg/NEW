# Campaign IV — Established limitations and open boundaries

**Definitions:** `LIMIT_ESTABLISHED_LOGICAL` = an information/authority impossibility under explicit premises; `EXTERNAL_CONTRACT_REQUIRED` = external mechanism needed but its real implementation unverified; `EMPIRICAL_OPEN` = unresolved choice of boundary mechanism. Nothing here grants trust to a source simply because it is signed.

## L-01 — Signed attestations do not imply external physical truth

**Status: LIMIT_ESTABLISHED_LOGICAL.** Observations: P3-P1 and P3-P2, verified in [P3_MIDPOINT_II.md](findings/P3_MIDPOINT_II.md). Signed payload is the same whether the *untransmitted* external truth label is true or false; the kernel cannot distinguish these worlds. This proves an information boundary, **not** a crypto vulnerability or sufficient proof of source independence. **K retains** provenance, exact subject, method, freshness, coverage, independence eligibility, closure decision. **T supplies** qualified measurement and its trustworthy provenance/coverage. **U** may supply measurement data but cannot unilaterally qualify its own claim to open rights. **Counterfactual:** include verifiable source-specific evidence in input and verify it separately; whether available and sufficient is still open.

## L-02 — Pure software judgment cannot enforce physical egress itself

**Status: LIMIT_ESTABLISHED_LOGICAL under premise 'pure kernel has no privileged network/provider credentials'.** A deterministic judgment returns authorization, not a physical barrier against an adversary with bypass credentials. **K** specifies and rejudges exact authorized effect. **T** enforces credential exclusivity, egress and provider semantics. This is a consequence of the capability split in [SCOPE.md](SCOPE.md), **not experimentally proven** for deployed Standard (G09/G15 remain OPEN).

## L-03 — A hash alone cannot show that the physical actor is a distinct human

**Status: LIMIT_ESTABLISHED_LOGICAL under premise 'kernel observes only logical signed identities and keys'.** A quorum on distinct keys does not logically establish independent real humans if one physical actor possesses multiple keys. **K** enforces logical quorum and roles. **T** establishes bindings/custody/authentication. **Actual physical separation: EMPIRICAL_OPEN.**

## L-04 — Rollback resistance requires an independent durable anchor

**Status: EXTERNAL_CONTRACT_REQUIRED; physical threat model OPEN.** If the adversary rolls back every available state/pin and the evaluator has no independent durable memory, an old but valid snapshot is indistinguishable from a genuine earlier state. **K** rejects invalid histories when given anchors; **T** protects independent anchors against common-mode rollback. No real multi-host restore experiment has established the deployment contract.

## L-05 — No fair progress can be deduced from authorization alone

**Status: LIMIT_ESTABLISHED_LOGICAL under premise 'kernel neither schedules agents nor controls the availability of tools'.** A correct permission verdict is not a guarantee that an external actor eventually runs. **K** enforces obligation, permission, escalation and closure semantics; **T/U** must actually supply observable execution/liveness. Exact guarantees under external outages stay EMPIRICAL_OPEN (G08/G16).

## Limits NOT established

Exactly-once remote effect under provider ambiguity; concurrent multi-host fencing; independence of two deployed judges; real source coverage/truth; stable obligations under repeated repairs; bootstrap runtime/key custody; verified no alternative egress. These remain OPEN and require experiments or an explicit, testable external contract.

## Statut de clôture fonctionnelle (2026-10-09)

Voir [FUNCTIONAL_BOUNDARY_FREEZE_DECISION.md](FUNCTIONAL_BOUNDARY_FREEZE_DECISION.md) : **16/16 allocations K/T/U figées conditionnellement**, sans certification des garanties ni du déploiement. Les constatations et limites ci-dessus restent valables comme faits historiques/conditions d'audit ; elles ne constituent plus un blocage de **délimitation du noyau**. La validation physique, les preuves empiriques et les portes de sortie de P3 restent ouvertes ; G08/G16 ne doivent pas provoquer une nouvelle boucle d'audit général du produit.
