# Consolidation des branches — 9 octobre 2026

> Ce document décrit la consolidation initiale, qui avait conservé le WIP sans l'activer. Après correction de ce choix, la refonte `e6ec30e` est reprise dans le code actif avec alignement des tests, dépendances, workflow et docs. Les deux anciennes branches de développement ont été supprimées ; leurs commits restent accessibles. Voir [M2.md](M2.md) et la validation courante. Les constats ci-dessous expliquent les points d'intégration alors manquants ; ils ne sont pas tous des limites encore actuelles.

## Périmètre examiné

Inventaire distant complet avant consolidation : trois branches, sans autre
branche de travail. Base de `main` : `9b1fe507f718ef49c624f940c2d1f14ca08809d4`.

| Branche | Tête examinée | Décision |
|---|---|---|
| `main` | `9b1fe507f718ef49c624f940c2d1f14ca08809d4` | Conserver le comportement actif et ses garanties |
| `design/coeur-stable-18-constats` | `b1b900130175dd8819b7ae43068b895708a1b4fb` | Intégrer les deux commits documentaires, puis supprimer la branche |
| `m2-tour2` | `d533e5663d4bfe9fa9dfaf243f330b83aaf18bf4` | Porter les reproductions ; conserver la refonte WIP dans l'ascendance Git sans activer son runtime ; supprimer la branche |

## Changements portés

- `docs/COEUR-STABLE.md` et son lien dans le README : cinq contrats, les
  correspondances R01–R18, les frontières et les critères de validation.
- Le commit `d533e5663d4bfe9fa9dfaf243f330b83aaf18bf4` : 21 fichiers,
  680 lignes de reproductions et de contexte sous `validation/review-m2/`.
  Ces scripts sont historiques ; ils ne deviennent pas des tests de réussite
  du runtime actuel et restent hors de `make test`.

Leurs sources sont conservées telles quelles. Le README historique de ces
reproductions décrit les conditions de leur revue, y compris une neutralisation
de seccomp dans leur ancien environnement. Ce n'est pas une procédure approuvée
pour exécuter Standard : la validation de cette consolidation garde seccomp actif.

## Pourquoi la refonte WIP n'est pas activée

Le commit expérimental
[`e6ec30e`](https://github.com/ichamafif-svg/NEW/commit/e6ec30e)
remplace la fusion de PR par une transition `base → head`, introduit des recettes
reproductibles, un runner de tests séparé, le retrait de propositions et une
mesure de lignée. Ces directions sont utiles pour la future refonte, mais
leur intégration actuelle n'est pas cohérente de bout en bout.

| Frontière | Résultat de l'examen |
|---|---|
| Suite existante | `make check` échoue dans `tests/test_m2.py` : trois tests transmettent encore `pr`/`method` au nouveau contrat et reçoivent `TYPE.ARGS` au lieu du refus de condition attendu |
| Workflow | Le workflow de démonstration lance toujours directement `scan`, alors que la branche exige des fichiers produits auparavant par `measure` et `test`. Les jobs et clés ne suivent pas le nouvel ordre simulé |
| Installation | `ops/probes.py` importe `yaml` et `ops/recipes.py` importe `packaging`, sans déclaration correspondante dans `requirements.txt` ; une installation propre n'est pas établie |
| Documentation | `docs/M2.md` décrit encore `remediate(area,item,pr,head,method)` et `review --pr`, tandis que le code utilise `base/head` et `review --head` |
| Destination | L'adaptateur fait GET puis PATCH de ref sans comparaison atomique du SHA de base. Sa garantie dépend de l'exclusivité du guard, affirmée mais non vérifiée par la seule présence de types de règles |
| Arbre comparé | `world.tree` retient seulement les blobs et leurs SHA : les modes et les gitlinks sont omis. La comparaison dite de l'arbre entier ne couvre donc pas toutes les modifications Git |
| Runner | Les tests utilisent une simulation du runner. Le runner réel installe/exécute le code et analyse un XML produit dans son environnement ; l'absence de clés revendiquée n'est pas une isolation démontrée par le launcher courant |
| Preuve et temps | Le checkout n'est toujours pas lié de façon vérifiée au snapshot distant ; le temps ops reste plafonné ; l'absence d'application constatée reste assimilée à une non-application définitive |

Il ne suffit pas de modifier les trois tests pour rendre cette refonte prête.
Elle change le contrat des floors, donc la release et la genèse applicables.
La consolidation ne choisit pas implicitement une nouvelle loi.

## Conservation intégrale du travail

Après le port du commit de reproductions, un merge de conservation avec la
stratégie Git `ours` inscrit `d533e5663d4bfe9fa9dfaf243f330b83aaf18bf4` comme
ancêtre de `main`, sans remplacer son arbre actif par l'expérience.
**Ce merge conserve l'historique ; il n'intègre pas fonctionnellement le WIP.**

Les commits expérimentaux et leurs fichiers restent accessibles par leurs SHA
et dans le graphe Git après suppression de la branche. On peut les examiner
dans un worktree détaché, puis porter des changements contre les contrats de
`COEUR-STABLE.md`. Aucun code expérimental n'est perdu, ni copié comme code mort
dans le runtime de `main`.

## Critères avant publication et suppression

- `make check` doit réussir sur l'arbre consolidé, avec confinement actif et
  budgets inchangés.
- Les sources du runtime, adaptateurs, loi, tests actifs, workflow et manifeste
  doivent être identiques à la base examinée.
- Les 21 fichiers de reproduction doivent être identiques à leur commit source.
- Les deux têtes distantes examinées doivent être ancêtres de la nouvelle `main`.
- La publication doit refuser si une branche a avancé depuis son examen ; aucun
  travail concurrent ne peut être supprimé sans être relu.
- La suppression distante intervient avec la publication validée de `main`.

Cette consolidation ne ferme aucun constat de sûreté de la revue V7/M2 et ne
revendique pas une mise en production. Elle fournit une seule branche active,
les preuves de revue et le travail expérimental conservé pour la refonte.

## Reprise après consolidation

La reprise rétablit les modules ops, l'adaptateur, les floors et les tests du tour 2. Les tests de contrat utilisent désormais `base/head` et les faits `tests/reproduced`. PyYAML et packaging sont déclarés. Le workflow produit les mesures/tests avant signature, sépare les jobs témoins et ne fournit pas de clé Standard aux instruments. Une transition retirée ne peut plus être rouverte par la recréation du même head.

Ces corrections lèvent les incohérences d'intégration identifiées dans la consolidation initiale. Les limites de modes Git, du runner, de compare-and-swap fournisseur, de temps et de preuves restent explicites dans M2 ; elles ne sont pas déclarées résolues. Le manifeste est régénéré pour la nouvelle identité de code ; aucune ancienne genèse n'est migrée implicitement.
