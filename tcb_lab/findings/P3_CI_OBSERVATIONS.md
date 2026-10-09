# Phase 3 — Première exploitation automatique des exécutions GitHub

**Preuves consultées :** GitHub Actions jobs de la branche de laboratoire et registre CI automatique (issue #2). **Ce document contient des constats OBSERVÉS, pas une évaluation générale de la sûreté.**

## Rétablissement de l'accès aux résultats

Le connecteur GitHub de recherche « workflows par SHA » interroge un sous-ensemble de runs et ne retrouvait pas les runs `push`. Nous avons désormais un **job CI secondaire** qui consulte l'API Actions, agrège l'historique des exécutions (y compris en rouge), récupère automatiquement les JSON d'attaque puis actualise l'issue [#2](https://github.com/ichamafif-svg/NEW/issues/2). Aucune manipulation de fichiers par l'utilisateur n'est nécessaire.

Avec les identifiants de runs publiés dans cette issue, le connecteur GitHub peut récupérer les jobs et les logs complets. Le job de rapport est distinct du job de tests : l'autorisation de publication d'issue ne doit pas être accessible au processus d'attaque.

## Constats observés

**P3-OBS-01 — faux vert du workflow expérimental** (**CONFIRMED** : défaut d'instrumentation CI, pas vulnérabilité constitutionnelle). Sur le run #19 (`37948321004`), la suite de mutations `p3_mutation_fuzz.py` a produit une traceback, mais le job de test restait marqué success. Cause directe : `python … | tee fichier` sans `pipefail` explicite ; le code de sortie de Python pouvait être masqué par `tee`. Action dans la branche : préciser `shell: bash` pour les six étapes de tests afin de faire appliquer `-e -o pipefail`. **À confirmer par le prochain run.**

**P3-OBS-02 — oracles d'expérience incompatibles avec l'état interne** (**CONFIRMED** : défaut de harnais). Les suites de mutations et plusieurs scénarios signalés `INCONCLUSIVE` tentaient `canon(w.state)`, alors que le snapshot interne contient des tuples (hors JSON canonique). Il ne s'agit pas d'une violation de canonicalisation d'une entrée, mais d'une erreur du test lui-même. Action : comparer une copie profonde du snapshot et non une représentation JSON, sans modifier la TCB. **À confirmer par exécution.**

**P3-OBS-03 — régression de maintenance sur `make check`** (**CONFIRMED**, périmètre non-core mais pertinent pour l'autonomie). Plusieurs runs rouges `TCB boundary checks` (par exemple #60, #59, #55, #53, #51, #50 et #49 selon le registre Actions) échouent au même test : `test_rule6_red_tests_withdraw_and_free_the_target` dans la suite existante. Les logs attestent qu'une proposition est retirée puis qu'une nouvelle cible semble immédiatement proposée, alors que l'assertion du test échoue. **Hypothèse** : défaut de recyclage d'un état de réparation/target, ou test mal aligné avec la politique attendue ; ni cause racine ni propriété violée ne sont encore établies. Ne pas masquer ce test et ne pas le patcher dans ce laboratoire.

**P3-OBS-04 — le vert de P3 ne signifie pas verdicts tous favorables.** Le registre de l'issue #2 a compté deux `INCONCLUSIVE` sur P3 signed (`P3-02`, `P3-07`), un sur compositions (`P3-X06`), et un fichier mutations non-JSON pour #19. Les corrections de harnais sont soumises ; les nouveaux résultats doivent être lus avant toute requalification.

## Suite de l'investigation

- Rechercher via le registre automatique les nouvelles exécutions et anomalies sur les six suites.
- Vérifier si la régression `test_rule6_red_tests_withdraw_and_free_the_target` est reproductible sur une base de code non altérée avant de l'attribuer au cœur constitutionnel.
- Conserver les modes de panne `false green` et `autonomy repair withdraw` dans les dimensions de couverture de P3, sans les assimiler arbitrairement à des vulnérabilités FLOOR-0.
- P3 reste ouverte. Le choix de la représentation vNext demeure hors phase 3.

## Validation observée après correction des harnais

Le run P3 **#30**, GitHub Actions `37948915737`, a été automatiquement lu dans l'issue #2 avec verdict du job de test **success** et les six artefacts JSON **PARSED** : G1 4/4, signed 8/8, effects 4/4, mutations 30/30, autonomy 10/10, compositions 7/7, **aucun identifiant signalé**. Soit **59 exercices P3 exécutés** et quatre expériences G1, sous les hypothèses locales des fixtures. Cela prouve un fonctionnement de ces scénarios sur ce run, non une sûreté globale ni les frontières physiques non testées. Les runs `TCB boundary checks` restent une piste distincte : l'échec récurrent `test_rule6_red_tests_withdraw_and_free_the_target` ne doit pas être effacé par le vert de P3.

Lien : https://github.com/ichamafif-svg/NEW/actions/runs/37948915737 et https://github.com/ichamafif-svg/NEW/issues/2.

## Consolidation de statut — 9 octobre 2026

La suite des corrections instrumentales a produit ensuite des runs complets avec oracles analysables : voir [EV03–EV05](P3_EVIDENCE_REGISTER.md), notamment [Actions #45](https://github.com/ichamafif-svg/NEW/actions/runs/37951191335). Les constats OBS-01/02 sur la **qualité de mesure** restent historiques, mais les anciennes mentions « à confirmer » ne doivent pas être lues comme le statut du dernier run. Les résultats de 69 cas P3 sont **locaux et conditionnels**.

Le test historique rouge OBS-03 reste une **question ouverte** malgré certains boundary runs verts. Voir [P3_MIDPOINT.md](P3_MIDPOINT.md) puis [P3_DEPTH_COVERAGE_BACKLOG.md](P3_DEPTH_COVERAGE_BACKLOG.md). Ne pas présenter une alternance de runs sur des commits différents comme un comportement non déterministe sur le même binaire. La phase 3 reste exploration uniquement.
