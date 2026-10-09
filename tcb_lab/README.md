# Standard — Laboratoire expérimental TCB

**Branche :** `research/tcb-lab-scope-frozen`  
**Base de référence :** `main@d6347dccec714c0193bbc43af5de7e96e3a9ad27`  
**Statut :** laboratoire de recherche, non déployable.

## Mandat exclusif

Recherche sur la **Trusted Computing Base (TCB)** de Standard : noyau déterministe, mécanismes et dépendances de confiance indispensables à ses garanties. **Aucun développement** de produit, agent, orchestration M2, console, dashboard, intégration métier ou nouvelle fonctionnalité de maintenance dans cette branche.

Le code historique de `main` présent dans l'arbre est **un corpus de référence**, non une architecture à conserver. Aucune compatibilité avec les anciens formats, API, journaux, genèses ou modules n'est requise ; chaque garantie démontrée doit toutefois être préservée ou renforcée.

## Ce qui est figé

`SCOPE.md` définit les **sept responsabilités** (Identity, Authority, Law, State, Evidence, Obligation, Effect), les trois périmètres (décision, infrastructure de confiance, autonomie non souveraine), les cinq contrats transversaux, les garanties planchers et les critères de complétude. Le périmètre de responsabilités est figé ; sa complétude reste **à démontrer**.

`RESEARCH_PROTOCOL.md` prescrit la séquence : compléter/valider les garanties et les frontières → campagnes adversariales → inventaire → regroupement des causes racines → recherche de nouvelles abstractions → comparaison rigoureuse → prototype → nouvelle campagne.

## Ce qui demeure libre

Nombre de concepts internes, représentation constitutionnelle, DSL/CIR, algèbre de transitions, moteur de contrats, structure du noyau, langages, modules, protocoles et persistance. **Aucune abstraction n'est privilégiée ou adoptée par défaut.** L'algèbre de transitions essayée sur une autre branche n'est qu'une hypothèse, pas une fondation.

## Règles de laboratoire

- Préserver `main` et la branche `feat/vnext-deterministic-core` : pas de fusion ni modification implicite.
- Regrouper les expériences dans `tcb_lab/experiments/` et leurs résultats dans `tcb_lab/findings/`, avec hypothèse, scénario, procédure reproductible, résultat observé, dépendances et limitation.
- Séparer **OBSERVÉ**, **HYPOTHÈSE**, **NON TESTÉ** et **VALIDÉ**. Une documentation ou un test écrit mais non exécuté ne vaut pas validation.
- Les réductions de taille ne sont pas un objectif autonome : mesurer la TCB effective et les hypothèses externes.
- Ne pas confondre containment provisoire d'une vulnérabilité et correction architecturale.
- Ne pas mapper prématurément les sept responsabilités vers une algèbre ou un IR.
- Les preuves de non-régression doivent être comportementales **et** couvrir les frontières d'effet, de temps, de stockage, de preuve et de déploiement.

## Portes

**G0 — Scope fixé : OUI (contrat de responsabilités).**  
**G1 — Complétude démontrée : NON.**  
**G2 — Recherche adversariale exhaustive : NON.**  
**G3 — Causes racines consolidées : NON.**  
**G4 — Choix d'abstraction : INTERDIT avant G1–G3.**  
**G5 — Noyau candidat validé : NON.**

Le but est de découvrir **la meilleure abstraction pour satisfaire les garanties**, non de réécrire l'existant avec d'autres noms.

## Phase 3 — campagne active (9 octobre 2026)

Plan complet des huit phases : [PLAN.md](PLAN.md). Inventaire des garanties : [GUARANTEE_MATRIX.md](GUARANTEE_MATRIX.md). Hypothèses de menace : [THREAT_MODEL.md](THREAT_MODEL.md). Campagne adversariale, scénarios et limites : [ATTACK_CATALOG.md](ATTACK_CATALOG.md).

Les suites `experiments/p3_signed_core.py` et `experiments/p3_effect_line.py` fournissent **12 exercices adversariaux** (huit sur les décisions signées et quatre sur les frontières d'effet). Les scénarios complémentaires du catalogue exigent encore des harness dédiés, notamment pour multi-hôte, fournisseur et restauration. `python tcb_lab/experiments/g1_decision_probes.py` constitue une première expérience de scope additionnelle.

Une CI lecture seule `.github/workflows/tcb-lab-p3.yml` exécute ces suites sur un environnement isolé sans clés Standard ni droit d'écriture. **Aucun succès d'exécution n'est revendiqué tant que les logs ne sont pas vérifiés.** Les résultats sont distingués des hypothèses de lecture de code. Les phases 1–2 restent ouvertes à l'affinement, la phase 3 est en cours et **aucune abstraction centrale n'a été adoptée**.

## Phase 3 — extension adversariale à grande échelle

La campagne possède désormais [80 nouvelles hypothèses structurées](ATTACK_EXPANSION.md) en plus des [24 scénarios initiaux](ATTACK_CATALOG.md), soit **104 hypothèses d'attaque distinctement répertoriées**. Trois axes de tests supplémentaires sont ajoutés : `experiments/p3_mutation_fuzz.py` (**30 mutations signées**), `experiments/p3_autonomy.py` (**10 expériences autorité/progrès**), et le [modèle de menace de l'autonomie](AUTONOMY_THREAT_MODEL.md).

Au total, **52 exercices locaux sont codés dans les quatre scripts P3** : huit entrées signées, quatre effets locaux, trente mutations et dix expériences sur l'autonomie. Les quatre expériences G1 restent séparées. Les hypothèses non codées restent une file de recherche, et non des résultats. La CI déclenche ces suites sur push. L'accès GitHub disponible ici ne fournit pas encore de compte rendu d'exécution validé : **aucun résultat vert ni vulnérabilité confirmée n'est annoncé**.

L'objectif de Standard est l'**autonomie gouvernée**, pas seulement le refus de toute action : chaque campagne doit examiner si un agent habilité peut progresser en respectant les protections, et si toute impossibilité de progresser devient un état, une obligation ou une escalade explicite. Le noyau ne devient pas pour autant le scheduler ou l'agent.

## Phase 3 — profondeur bloquante, pas course au volume

La nouvelle [P3_EXIT_CRITERIA.md](P3_EXIT_CRITERIA.md) définit huit **portes de clôture obligatoires**. La [COVERAGE_DEPTH.md](COVERAGE_DEPTH.md) rend visibles les trous entre les seize familles de garanties et les cinq dimensions : décision, composition, panne, confiance physique et progression autonome. Chaque cellule `Coded` reste distincte d'un résultat exécuté.

`experiments/p3_compositions.py` ajoute **sept séquences adversariales composées** sur les restrictions, les jetons, les effets inconnus, les preuves et la continuité du travail légitime. La CI inclut ces séquences. Cela porte le laboratoire à **59 exercices P3 codés**, toujours **non validés par un run observé**. Les hypothèses recensées restent au nombre de 104 ; les exercices ne correspondent pas nécessairement un-pour-un aux hypothèses.

**La phase 3 demeure ouverte jusqu'à satisfaction des portes, pas jusqu'à un quota arbitraire de tests.** Le moteur d'autonomie reste extérieur au noyau constitutionnel, mais tout mécanisme autorisant ou clôturant ses effets doit être éprouvé dans la frontière de confiance.

## Phase 3 — recherche ouverte (pas de design)

[P3_EXPLORATION_PROTOCOL.md](P3_EXPLORATION_PROTOCOL.md) formalise la boucle **observation → question → hypothèses alternatives → contre-expérience → nouvelles questions**. Les résultats ne déclenchent ni refonte du scope ni choix d'abstraction. `experiments/p3_counterexperiments.py` ajoute cinq expériences couplées opposant perturbation hostile et voie de progression légitime, désormais incluses dans la CI et le registre automatique GitHub issue #2. Cela donne **64 expériences P3 codées**, plus les quatre G1. Toute interprétation doit rester conditionnelle aux traces effectivement observées.
