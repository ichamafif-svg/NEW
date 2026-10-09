> **NOTE DE LECTURE — 2026-10-09.** Ce document conserve son contenu historique. Pour l'état **actuel**, consulter [l'accueil canonique](README.md), [la charte / transfert](LAB_CHARTER_AND_HANDOFF.md) et [la décision fonctionnelle 16/16](FUNCTIONAL_BOUNDARY_FREEZE_DECISION.md). Les étapes de comparaison architecturale A/B/C ou les verdicts 14/2 éventuellement mentionnés ci-dessous ne sont **plus** la feuille de route active. La production du noyau hybride est sur la branche `prototype/hybrid-kernel-v1`, non dans le lab ; les critères P3 physiques restent ouverts.

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

## IV-B — revue des frontières et critères de fermeture

La [revue IV-B](IVB_BOUNDARY_CLOSURE.md) classe séparément les frontières `CLOSED_CONDITIONAL`, `OPEN_CRITICAL` et `OPEN_SEMANTIC` pour **G01–G16**, avec les contre-exemples et dépendances physiques. Quatre nouvelles expériences signées (effet révoqué, retry inconnu, preuve bon/mauvais sujet) sont intégrées à la CI via `p3_ivb_boundary_pairs.py`. **La classification ne constitue pas une validation de sûreté ; aucun scope ou noyau n'a été modifié.**

## Campagne IV-C — conclusion de délimitation (pas une preuve physique)

[IVC_BOUNDARY_DECISIONS.md](IVC_BOUNDARY_DECISIONS.md) passe en revue les **12 frontières antérieurement ouvertes** : dix allocations K/T/U deviennent **conditionnelles** sur la base de leurs contrats d'information et d'application ; **G08** (continuité des obligations) et **G16** (progression autonome) restent sémantiquement ouvertes. Avec les quatre allocations déjà conditionnelles en IV-B, on obtient **14 délimitations conditionnelles / 2 ouvertes**, *et non 14 garanties vérifiées*. Les contrats externes restent non validés physiquement. `p3_ivc_scope_audit.py` vérifie seulement la cohérence documentaire dans la CI, sans se substituer aux expériences adversariales manquantes. Aucun changement du scope sémantique [SCOPE.md](SCOPE.md) ou du noyau.

## IV-D — revue des blocages G08 / G16

Le découpage actuel reste 14 `CLOSED_CONDITIONAL` / 2 `OPEN_SEMANTIC` (G08, G16). [P3_G08_G16_CAMPAIGN.md](findings/P3_G08_G16_CAMPAIGN.md) fixe les hypothèses, témoins, raisons de non-clôture et nouvelles traces sur 20 cycles. **Aucun changement de scope**, aucune sélection d'abstraction ; la revue finale est suspendue à la preuve d'identité/durée d'une obligation et à l'oracle de progression ou escalade.

## G08/G16 — lecture des résultats réels (après Actions 37964069387)

Voir [l'interprétation complète](findings/P3_G08_G16_FIRST_INTERPRETATION.md). Dans les scénarios à écart persistant, deux propositions sont retirées puis **18 cycles / 20 sans sujet live** sont observés, sans modification de main. Les obligations constitutionnelles ne peuvent pas être déduites de la seule liste `state["obligations"]` vide : **G08 reste ouvert**. **G16 reste ouvert** en attente du contrôle des escalades et de la fairness. Le prétendu contrôle sain était **invalide** (le runner `none` n'enlevait pas `vulns=found:2`) et a été rectifié dans le harnais ; ne pas citer l'ancien résultat comme témoin sain. Aucune modification du noyau ou du scope.

## Décision de consolidation — 9 octobre 2026 (statut actuel du **découpage**)

La [décision canonique de frontière fonctionnelle](FUNCTIONAL_BOUNDARY_FREEZE_DECISION.md) attribue désormais **16/16 garanties G01–G16 à K (décisions du noyau), T (Trusted External) et U (autonomie remplaçable)** sous hypothèses explicites. **Statut : CONDITIONAL_BOUNDARY_FROZEN**, et **non** 16 garanties prouvées. Les anciennes mentions `14 conditionnelles / 2 ouvertes` ou `OPEN_SEMANTIC` pour G08/G16 décrivent **l'étape IV-C/IV-D historique** et sont supplantées **uniquement pour la délimitation fonctionnelle** ; elles restent utiles comme état des preuves à leur date. G08 : dette canonique indépendante des tentatives ; G16 : règles de permission, dette et exigibilité d'escalade dans K, scheduling/retries/notification dans U et préconditions fiables dans T. La campagne IV-I et les travaux d'implémentation ne bloquent **pas** la décision de découpage. Le scope sémantique `SCOPE.md` demeure intact ; l'assurance physique, l'audit de déploiement et les portes de sortie P3 restent **ouverts**. Ne pas relancer une boucle de recherche sur tout Standard sans contre-exemple démontrant une mauvaise attribution K/T/U.
