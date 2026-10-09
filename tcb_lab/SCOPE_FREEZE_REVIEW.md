# Campaign IV — Functional scope freeze review

**Scope responsibilities were already frozen in [SCOPE.md](SCOPE.md); campaign IV tests their *allocation*, completeness and external limits.** Do not silently modify the earlier freeze or select an internal representation. This document is a **checkpoint**, not authorization to finalize architectural scope.

| Check | Current assessment | Blocking missing evidence |
|---|---|---|
| Seven semantic responsibilities | **BASELINED** (Identity/Authority/Law/State/Evidence/Obligation/Effect) | interactions, minimality and non-regression not fully proven |
| Three trust zones (K/T/U) | **BASELINED** | physical perimeter of T (G05/G09/G10/G11/G15) not exhaustively verified |
| 16 guarantees assigned K/T/U | **CLASSIFIED PROVISIONALLY** in [TCB_BOUNDARY_MATRIX.md](TCB_BOUNDARY_MATRIX.md) | independent falsifying controls for each line |
| Information-theoretic external limits | **CONDITIONAL LIMITS DOCUMENTED** in [ESTABLISHED_LIMITS.md](ESTABLISHED_LIMITS.md) | externally verifiable source contracts |
| Adversarial experiment coverage | **ACTIVE** | same-subject obligations; proof qualification; multi-process/host and crash tests |
| Design/abstraction chosen | **NO — OUT OF PHASE 3** | not applicable |

**Decision: FUNCTIONAL SCOPE REMAINS FROZEN AS PRIOR BASELINE; BOUNDARY VALIDATION INCOMPLETE.** The target of campaign IV is to conclude conditional boundary contracts and list true blockers, not to mark all guarantees proved by assertion. Review status per Gxx remains `PROVISIONAL` until a run-specific trace and counterfactual show that another classification could not satisfy the guarantee.

## Prioritized discriminating research

1. **E/G09/G10/G15**: isolate one-shot replay refusal using valid time, then identify real enforcement site, test bypass credential path, process concurrency and ACK ambiguity.
2. **O/G08/G16**: same subject over repeated withdrawal/repair and shifting target, capture due/opened/reasons; distinguish legitimate new attempt from unbounded churn.
3. **P/G07/G12/G13**: independently checked proof methods/coverage and common-mode compromise, not just signed external false label.
4. **A/L/T/B**: key ownership, quorum, time, signed prefix and independent pin/failover, working across real trust zones.

**No physical boundary is waived because a local test is green.**
