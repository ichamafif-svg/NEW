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
