# Phase 3 — Findings : état consolidé et navigation

**Date d'observation : 2026-10-09. Corpus :** `research/tcb-lab-scope-frozen`, noyau historique `main@d6347dc`. **Statut : exploration ouverte, non-conception.**

## Lire les résultats correctement

Une *exécution CI verte* décrit la réussite du pipeline, et non la preuve de sûreté de la TCB. Une *expérience locale verte* indique que le scénario hostile a été bloqué ou que le contrôle positif est passé **sous les hypothèses du harnais**. Une *croix rouge* signifie un échec d'exécution qui doit être attribué : instrumentation, test, attente, dépendance ou violation de propriété.

Source vivante des runs, dont les rouges : [registre Actions #2](https://github.com/ichamafif-svg/NEW/issues/2). Historique détaillé et logs : GitHub Actions run IDs. Ce répertoire contient des instantanés **datés**, qui ne remplacent pas la source automatique.

## Carte des documents

| Document | Objet | Niveau de certitude |
|---|---|---|
| [P3_CI_OBSERVATIONS.md](P3_CI_OBSERVATIONS.md) | Chronologie et causes connues des faux verts et échecs historiques | Observations des logs + hypothèses séparées |
| [P3_LONG_HORIZON_QUESTIONS.md](P3_LONG_HORIZON_QUESTIONS.md) | Cinq séquences de 80 tentatives et questions ouvertes | Résultats locaux seulement |
| [P3_MIDPOINT.md](P3_MIDPOINT.md) | Ce que l'ensemble des réussites et échecs permet **et ne permet pas** de conclure | Synthèse conditionnelle |
| [P3_EVIDENCE_REGISTER.md](P3_EVIDENCE_REGISTER.md) | Sources, runs, périmètres, limites de chaque affirmation | Provenance reproductible |
| [P3_DEPTH_COVERAGE_BACKLOG.md](P3_DEPTH_COVERAGE_BACKLOG.md) | Où creuser ensuite ; arbre profondeur × couverture, priorités et critères d'expérience | Questions NOT_RUN explicitement |
| [../EXPERIMENT_TREE_DEPTH_COVERAGE.md](../EXPERIMENT_TREE_DEPTH_COVERAGE.md) | Arbre de référence à huit branches et niveaux D0–D7 | Carte des tests, pas validation |

## Synthèse en une phrase

**Ce qui fonctionne dans les fixtures locales ne démontre pas encore l'autonomie gouvernée du dépôt entier.** Les explorations doivent monter en *profondeur* (séquences du même sujet, pannes, races, domaines physiques) et en *couverture* (preuves, obligations, privilèges, BUILD/RUN et frontières de confiance). Les résultats ne servent ni à modifier le scope, ni à sélectionner une abstraction, ni à patcher l'architecture.

## Statut de l'étape

**Phase 3 : ACTIVE.** Pas de pourcentage artificiel d'achèvement, pas de déclaration « béton ». La prochaine action se déduit des trous expérimentaux dans [P3_DEPTH_COVERAGE_BACKLOG.md](P3_DEPTH_COVERAGE_BACKLOG.md).
