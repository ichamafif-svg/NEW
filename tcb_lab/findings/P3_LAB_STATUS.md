# Phase 3 — État vivant du laboratoire

**Version datée : 2026-10-09.** En cas de désaccord, les résultats d'Actions et les fichiers de preuve datés prévalent sur un README historique. Ce fichier n'est pas un statut produit.

## Ce que l'on sait

- Les tests locaux antérieurs ont exercé décisions signées, effet synthétique, mutations, autonomie et compositions avec oracles limités.
- Les résultats de campagne II ont identifié **dix divergences sur dix** avec l'assertion historique `no_live` à deux cycles (`withdrawn` + nouveau `measuring`).
- Les huit seconds `redeem` de campagne II étaient refusés au motif `HIST.TIME` : **aucune preuve anti-double effet ne doit en être déduite**.
- Le noyau rejette certains mauvais auteurs/sujets/niveaux/horodatages d'attestation, mais le drapeau de vérité externe n'est pas transmis et ne peut être jugé par le noyau.
- La frontière fournisseur est synthétique et SQLite est local ; la frontière physique n'est pas établie.

## Ce qui démarre maintenant

Campagne III : 8 expériences d'effet à temps post-commit, 18 expériences d'identité de sujets pendant la maintenance et 6 contrastes épistémiques de preuves. **32 cas codés et soumis en CI ; ne pas les annoncer exécutés avant confirmation du run.** Les sorties sont ajoutées automatiquement au registre #2.

## Documents directeurs

[Arbre profondeur × couverture](../EXPERIMENT_TREE_DEPTH_COVERAGE.md) → [midpoint II](P3_MIDPOINT_II.md) → [campagne III](P3_CAMPAIGN_III.md) → [backlog](P3_DEPTH_COVERAGE_BACKLOG.md) → [preuves CI](P3_EVIDENCE_REGISTER.md) → [gate de recherche](../P3_EXIT_CRITERIA.md).

**Interdit :** patcher la TCB historique, réduire le scope, choisir CIR/DSL/algèbre, interpréter un vert CI comme une preuve de sûreté.

## Vérification post-correction — 9 octobre 2026

Le [run Actions `37956022363`](https://github.com/ichamafif-svg/NEW/actions/runs/37956022363) est **success** avec artefacts III **PARSED** : E=8 observations, O/R=18 observations, P=6 observations, zéro cas III classé inconclusif dans le registre. L'erreur JSON du premier run est donc résolue pour ce run ; elle reste conservée comme constat d'instrumentation. **Ne pas confondre ce succès CI avec une validation de safety/liveness :** les expériences O/R sont descriptives, le fournisseur E est simulé, et le label de vérité P ne figure pas dans la déclaration signée. Les runs historiques continuent de présenter des divergences aux assertions de cycle ; les trois sous-arbres demeurent **ouverts**.
