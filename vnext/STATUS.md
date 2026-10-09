# vNext — première implémentation du noyau déterministe

Base : `main@d6347dccec714c0193bbc43af5de7e96e3a9ad27`.
Scope normatif figé : branche `research/tcb-scope-vnext`, fichiers `SCOPE.md` et `RESEARCH_PROTOCOL.md`.

Cette branche **contient l'ensemble du code de main** et ajoute une première surface d'exécution pure dans `vnext/decision.py`. Aucune compatibilité avec les anciennes genèses, formats ou API n'est imposée à la future implémentation. Le code historique sert de référence de garanties pendant la recherche.

## Réalisé

- `DeterministicCore.evaluate(state, signed_entry)` : entrée canonique, jugement constitutionnel réel issu de `main`, contrôle par le second juge indépendant, validation d'absence de mutation des arguments et calcul du delta sur une copie.
- `Decision` : résultat constitué d'octets immuables et de digests liés au code, à l'état avant/après, à la loi et à l'entrée.
- `preview` : projection du delta uniquement sur son prédécesseur exact, sans accès fournisseur ni persistance.
- `replay` : réduction déterministe des entrées avec une instance neuve du moteur par décision.
- `tests/test_vnext_decision.py` : déterminisme, absence de mutation, refus d'une restriction non autorisée, protection contre le rejeu d'un aperçu et entrées malformées.

## Limites et règles de sécurité

**Il s'agit d'une première extraction exécutable, pas d'un remplacement vNext certifié.** Les sept responsabilités constitutionnelles ne sont pas encore réimplémentées dans une abstraction neuve ; la sémantique héritée, y compris la couverture partielle du second vérificateur, demeure. L'infrastructure de confiance n'est pas remplacée.

Une `Decision` n'est **jamais** un mandat, un token, une réservation ou une autorisation d'envoi. Le journal et le guard de main restent les seuls chemins d'admission et d'effet physique existants.

Le nouveau dossier `vnext/` n'est pas couvert par le manifeste de confiance historique ; l'interface n'est donc pas activable en production sans définir une nouvelle chaîne d'amorçage, une nouvelle genèse et une frontière de contrôle exclusif. Aucune garantie de production additionnelle n'est revendiquée.

## Validation

Commande prévue : `python3 tests/test_vnext_decision.py`. La suite historique : `make check`.

**Tests vNext non exécutés dans l'environnement de création.** Ne pas confondre présence des tests et réussite de leur exécution. La suite de main n'a pas été exécutée à nouveau ici.

## Prochaine phase

1. Faire passer les tests et corriger les problèmes de frontière, sans patcher des symptômes de sécurité.
2. Formaliser la matrice des garanties historiques et les entrées/sorties des sept responsabilités.
3. Auditer la complétude du scope, en incluant la TCB effective et les composants de preuve externes.
4. Réaliser les recherches adversariales groupées, puis seulement rechercher une abstraction plus simple.

## Differential equivalence gate (added)

`python tools/compare_vnext.py` runs **the same 19 historical test scripts twice**: unmodified `main` behavior, then the *same scripts* with a shadow hook intercepting `Kernel.decide`. Every intercepted admitted decision compares canonical record and ordered delta; refusals compare exact refusal code. The hook returns the original decision to keep the test's behavior unchanged. It writes `validation/vnext-differential.json`. A new push-triggered workflow at `.github/workflows/vnext-parity.yml` runs both this parity gate and `tests/test_vnext_decision.py`.

**Not yet measured:** neither local results nor CI results have been observed at documentation time. A passing shadow comparison would establish test-suite behavioral parity for intercepted paths, **not** independent assurance: vNext still delegates its judgement to the historical kernel and shares its trust dependencies. Other guarantees (effect isolation, provider atomicity, durable pins and deployments) require separate evaluation.

## Focus: constitutional TCB, not orchestration (current iteration)

- Frozen requirements and research rules are copied into `vnext/SCOPE.md` and `vnext/RESEARCH_PROTOCOL.md`.
- `vnext/transition.py` implements a **generic, closed mutation algebra** over the canonical state, independent of permissions/agents/providers. Every instruction is shape-checked and produces a post-state digest; exhaustive equality verifies the declared state change.
- `vnext/decision.py` compares this independent interpreter with the historical `tcb.kernel.apply` before returning any accepted result. A disagreement refuses the transition, rather than altering the legacy execution path.
- `tests/test_vnext_transition.py` tests mutation completeness, fail-closed grammar and deterministic trace; the vNext CI script invokes it.

**Important:** this is a concrete step toward a better abstraction (constitution = typed transition contract + authority/evidence predicates + controlled effect), not completion. The constitutional judge still relies on main's semantics and does not yet implement a new seven-responsibility decision model. This branch has not passed an independently observed full validation run and MUST NOT replace production admission.
