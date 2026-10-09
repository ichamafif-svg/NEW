# Campagne IV — délimitation des frontières et scope fonctionnel

**Date : 2026-10-09.** **Objectif :** accélérer la clôture des *questions de répartition des responsabilités* sans confondre clôture d'une limite logique et validation d'une implémentation. **Le scope historique de [SCOPE.md](../SCOPE.md) reste figé et n'est pas modifié ici.** Ni abstraction nouvelle ni changement de la TCB historique.

## Travaux livrés

- [TCB_BOUNDARY_MATRIX.md](../TCB_BOUNDARY_MATRIX.md) : classement préliminaire des **16 garanties G01–G16** entre **K** (jugement constitutionnel), **T** (mécanisme externe dont la confiance est indispensable) et **U** (agent ou outil non souverain). Les responsabilités peuvent être partagées K+T ; externaliser la vérification physique ne la sort **pas** de la TCB effective.
- [ESTABLISHED_LIMITS.md](../ESTABLISHED_LIMITS.md) : limites logiques **conditionnelles** établies par information indisponible ou absence de capacité physique et dépendances encore non démontrées : vérité externe, egress, identité physique, rollback, progrès.
- [SCOPE_FREEZE_REVIEW.md](../SCOPE_FREEZE_REVIEW.md) : revue provisoire du scope fonctionnel préexistant, critères non acquis et expériences discriminantes restant à mener.
- `experiments/p3_iv_boundary_probes.py` : **trois** comparaisons observables sur preuves et effet simulé, sans prétention de couverture des seize garanties.
- `experiments/p3_iv_coverage_audit.py` : vérification automatisée de **complétude documentaire** G01–G16, absences/duplications/cellules vides, et avertissement contre un gel prématuré du scope. Il ne s'agit pas d'un test adversarial de chacune des 16 garanties.
- CI : runs automatiques, artefacts JSON, registre [issue #2](https://github.com/ichamafif-svg/NEW/issues/2). Le résultat n'est déclaré `OBSERVED` qu'après log/artefact vérifié.

## Conclusions retenues avec leur force exacte

**Limite logique établie (conditionnelle) :** la vérité externe absente du message signé ne peut pas être inférée par le noyau. Cela ne signifie pas que le noyau ne doit pas vérifier la qualification de la source, la méthode ou la couverture.

**Limite logique établie (conditionnelle) :** un calcul pur de permission, sans credentials ni contrôle des canaux d'egress, ne peut pas empêcher physiquement un acteur équipé d'autres credentials d'agir. L'intégrité de ces canaux reste une dépendance **de confiance** et doit être éprouvée.

**Frontières non prouvées :** exécution unique multi-hôte, qualité physique des sources de preuve, impossibilité de contourner tous les effets par un credential alternatif, dette persistante à travers rechutes multiples, restauration globale rollback-safe, indépendance réelle des signataires/juges.

## Décision de midpoint

**Le contrat de responsabilités K/T/U est cartographié pour G01–G16, mais pas encore expérimentalement fermé.** La prochaine profondeur doit tester en priorité les **interfaces de confiance** et les **hypothèses externes irréductibles**, plutôt que répéter les seules vérifications logiques locales. L'arbre de [PROFONDEUR × COUVERTURE × FRONTIÈRE](../EXPERIMENT_TREE_DEPTH_COVERAGE.md) garde la provenance de chaque affirmation et les manques explicites.

**Statut : campagne IV active ; pas de validation générale du scope et aucune transition vers le design.**
