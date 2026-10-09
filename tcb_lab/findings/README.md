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

## Première récolte des trois priorités

Lire [P3_PRIORITY_FIRST_RESULTS.md](P3_PRIORITY_FIRST_RESULTS.md) : les quatre témoins O1, quatre permutations d'effet E1 et trois expériences de preuve P1 ont été **observés dans des logs CI réels**. La réexécution du témoin rouge O1 à deux cycles donne cette fois les assertions satisfaites ; l'ancienne panne reste à expliquer. Le résultat le plus instructif sur P1 est la différence entre *signature sur bon sujet* et *vérité physique non attestée* ; sur E1, c'est la distinction entre `failed` et un effet vraiment non appliqué.

## Deuxième campagne de profondeur — résultats observés

[Plan et hypothèses](P3_SECOND_DEPTH_CAMPAIGN.md) · [Résultats et limites](P3_SECOND_DEPTH_RESULTS.md). Les trois familles approfondies sont **P1 (7 attestations), E1 (8 séquences port/journal) et O1 (16 variations de maintien/withdraw)**. Le run [#74](https://github.com/ichamafif-svg/NEW/actions/runs/37953933593) a publié 14 rapports JSON analysables sans expérience `INCONCLUSIVE` signalée. **Cela ne ferme aucune des trois priorités** : vérité physique, frontière de sortie et même cible en temps long exigent davantage d'attaques.

## Deuxième campagne — contradiction empirique

[P3_CAMPAIGN_II_CONTRADICTIONS.md](P3_CAMPAIGN_II_CONTRADICTIONS.md) documente **les résultats opposés du retrait après deux cycles sur plusieurs reprises dans un même run**, sans supposer un état initial identique, ainsi que les huit comparaisons de départ et sept variations de preuve. La campagne a également révélé que le rapport CI ne signalait pas les écarts `OBSERVED` vis-à-vis de l'assertion historique. La sortie automatisée a été enrichie pour afficher ces écarts plutôt que de les classer silencieusement parmi les tests verts.

## Midpoint II — interprétation des 31 nouvelles expériences

[P3_MIDPOINT_II.md](P3_MIDPOINT_II.md) reprend les **sorties individuelles** des 7 preuves, 8 effets et 16 séquences de maintenance, et rectifie la lecture trompeuse du vert CI : dix divergences historiques observées, refus de deuxième redemption uniquement `HIST.TIME` (oracle anti-doublon non isolé) et qualification de preuve sans accès à la vérité externe. Ce document est maintenant la référence pour la prochaine profondeur ; ne pas conclure sur une faiblesse structurelle ou une solution.

## Campagne III et arbre central

Lire [P3_LAB_STATUS.md](P3_LAB_STATUS.md) puis [P3_CAMPAIGN_III.md](P3_CAMPAIGN_III.md). Le référentiel de profondeur et couverture est [EXPERIMENT_TREE_DEPTH_COVERAGE.md](../EXPERIMENT_TREE_DEPTH_COVERAGE.md) ; la campagne III interroge précisément les limites de nos oracles précédents, sans effacer les résultats antérieurs.

## Campagne IV — limites et frontière effective

Pour distinguer ce qui relève de la décision du noyau, de la confiance physique externe et du travail remplaçable : [TCB_BOUNDARY_MATRIX.md](../TCB_BOUNDARY_MATRIX.md), [ESTABLISHED_LIMITS.md](../ESTABLISHED_LIMITS.md), [SCOPE_FREEZE_REVIEW.md](../SCOPE_FREEZE_REVIEW.md). **Classification provisoire ≠ démonstration de garanties G01–G16**. L'objectif est la stabilisation argumentée de la frontière, sans concevoir la représentation interne.

## IV-B — revue des frontières et critères de fermeture

La [revue IV-B](../IVB_BOUNDARY_CLOSURE.md) classe séparément les frontières `CLOSED_CONDITIONAL`, `OPEN_CRITICAL` et `OPEN_SEMANTIC` pour **G01–G16**, avec les contre-exemples et dépendances physiques. Quatre nouvelles expériences signées (effet révoqué, retry inconnu, preuve bon/mauvais sujet) sont intégrées à la CI via `p3_ivb_boundary_pairs.py`. **La classification ne constitue pas une validation de sûreté ; aucun scope ou noyau n'a été modifié.**

## IV-D — continuité des obligations et autonomie

[Nouveaux tests G08/G16](P3_G08_G16_CAMPAIGN.md) · [Consolidation et sources de vérité](P3_LAB_CHANGELOG.md) · [Registre CI](https://github.com/ichamafif-svg/NEW/issues/2). Conserver les findings antérieurs comme historiques, jamais comme preuve de la validation actuelle.

## G08/G16 — lecture des résultats réels (après Actions 37964069387)

Voir [l'interprétation complète](P3_G08_G16_FIRST_INTERPRETATION.md). Dans les scénarios à écart persistant, deux propositions sont retirées puis **18 cycles / 20 sans sujet live** sont observés, sans modification de main. Les obligations constitutionnelles ne peuvent pas être déduites de la seule liste `state["obligations"]` vide : **G08 reste ouvert**. **G16 reste ouvert** en attente du contrôle des escalades et de la fairness. Le prétendu contrôle sain était **invalide** (le runner `none` n'enlevait pas `vulns=found:2`) et a été rectifié dans le harnais ; ne pas citer l'ancien résultat comme témoin sain. Aucune modification du noyau ou du scope.

## Décision de consolidation — 9 octobre 2026 (statut actuel du **découpage**)

La [décision canonique de frontière fonctionnelle](../FUNCTIONAL_BOUNDARY_FREEZE_DECISION.md) attribue désormais **16/16 garanties G01–G16 à K (décisions du noyau), T (Trusted External) et U (autonomie remplaçable)** sous hypothèses explicites. **Statut : CONDITIONAL_BOUNDARY_FROZEN**, et **non** 16 garanties prouvées. Les anciennes mentions `14 conditionnelles / 2 ouvertes` ou `OPEN_SEMANTIC` pour G08/G16 décrivent **l'étape IV-C/IV-D historique** et sont supplantées **uniquement pour la délimitation fonctionnelle** ; elles restent utiles comme état des preuves à leur date. G08 : dette canonique indépendante des tentatives ; G16 : règles de permission, dette et exigibilité d'escalade dans K, scheduling/retries/notification dans U et préconditions fiables dans T. La campagne IV-I et les travaux d'implémentation ne bloquent **pas** la décision de découpage. Le scope sémantique `SCOPE.md` demeure intact ; l'assurance physique, l'audit de déploiement et les portes de sortie P3 restent **ouverts**. Ne pas relancer une boucle de recherche sur tout Standard sans contre-exemple démontrant une mauvaise attribution K/T/U.
