# Phase 3 — Campagne empirique P0 : trois priorités issues des findings

**Statut : démarrée, observations sous collecte CI.** Seul objectif : **profondeur × couverture**. Les résultats ne changent ni le scope, ni l'abstraction, ni le code du noyau.

## Couverture explicite des findings

| Priorité | Parents | Expériences lancées | Ce qui manque encore |
|---|---|---|---|
| **P0-1 O1/R1 — retrait réparation** | P3_CI_OBSERVATIONS OBS-03, P3_MIDPOINT, backlog #1, arbre O1 | `p3_priority_o1.py` rejoue le rouge, avec contrôle sain, 1/2/3 cycles, captures états et assertions historiques séparées | confirmer la nature de l'assertion; oblig. continue, deux agents, contrôles de priorité |
| **P0-2 E1 — effet inconnu** | P3_EFFECT_LINE, backlog #2, arbre E1 | `p3_priority_e1.py` compare timeout après appel, résultat unknown, ok, failed ; enregistre sends, dette et verdict retry | delayed ACK, crash, fencing multi-hôte, vrai provider |
| **P0-3 P1/O1 — preuve trompeuse** | G07/G13, backlog #3, arbre P1 | `p3_priority_p1.py` compare preuve vraie, fausse mais signée, mauvais sujet ; observe clôture indépendamment de vérité synthétique | preuve partielle, oracle commun, méthode/SHA, fausse couverture |

## Contrats d'analyse

- **Un résultat OBSERVED** signifie « on a mesuré le comportement », pas « c'est sûr ».
- **Une divergence avec le test historique** n'est pas par elle-même une faille TCB.
- **Une fausse attestation signée** peut montrer une hypothèse de confiance dans un oracle, pas une vulnérabilité du vérificateur de signatures.
- **Un retry refusé** peut préserver safety, mais il faut aussi tester si une réconciliation autorisée rend la progression possible.
- Chaque découverte ouvre un nouvel enfant de l'arbre ; rien ne déclenche refactoring ou changement constitutionnel.
- Les tests qui échouent à l'instrumentation sont `INCONCLUSIVE`, à reproduire avec erreur précise.

## Automatisation

Les trois suites nouvelles sont ajoutées au workflow `tcb-lab-p3.yml`, avec `continue-on-error` limité à la collecte complète et job final rouge si l'une échoue. Les trois rapports JSON sont joints aux artefacts et à l'[issue CI #2](https://github.com/ichamafif-svg/NEW/issues/2).

**À ne pas confondre avec une couverture exhaustive :** [P3_DEPTH_COVERAGE_BACKLOG.md](P3_DEPTH_COVERAGE_BACKLOG.md) garde neuf axes ; nous traitons maintenant ses trois premiers, et les autres restent explicitement ouverts.
