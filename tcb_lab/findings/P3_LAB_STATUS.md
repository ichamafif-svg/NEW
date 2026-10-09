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

## Campagne IV — état initial

Les 16 garanties ont désormais une allocation provisoire `K/T/U` dans [TCB_BOUNDARY_MATRIX.md](../TCB_BOUNDARY_MATRIX.md), avec plusieurs limites logiques conditionnelles dans [ESTABLISHED_LIMITS.md](../ESTABLISHED_LIMITS.md). La revue [SCOPE_FREEZE_REVIEW.md](../SCOPE_FREEZE_REVIEW.md) maintient les sept responsabilités historiques figées tout en signalant les validations physiques manquantes. Trois probes différentiels locaux supplémentaires sont intégrés en CI. **On n'annonce pas un nouveau scope figé par tests : on évalue le scope déjà figé.**

## Campagne IV-C — conclusion de délimitation (pas une preuve physique)

[IVC_BOUNDARY_DECISIONS.md](../IVC_BOUNDARY_DECISIONS.md) passe en revue les **12 frontières antérieurement ouvertes** : dix allocations K/T/U deviennent **conditionnelles** sur la base de leurs contrats d'information et d'application ; **G08** (continuité des obligations) et **G16** (progression autonome) restent sémantiquement ouvertes. Avec les quatre allocations déjà conditionnelles en IV-B, on obtient **14 délimitations conditionnelles / 2 ouvertes**, *et non 14 garanties vérifiées*. Les contrats externes restent non validés physiquement. `p3_ivc_scope_audit.py` vérifie seulement la cohérence documentaire dans la CI, sans se substituer aux expériences adversariales manquantes. Aucun changement du scope sémantique [SCOPE.md](../SCOPE.md) ou du noyau.
