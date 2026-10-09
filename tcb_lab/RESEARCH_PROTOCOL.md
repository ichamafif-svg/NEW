> **NOTE DE LECTURE — 2026-10-09.** Ce document conserve son contenu historique. Pour l'état **actuel**, consulter [l'accueil canonique](README.md), [la charte / transfert](LAB_CHARTER_AND_HANDOFF.md) et [la décision fonctionnelle 16/16](FUNCTIONAL_BOUNDARY_FREEZE_DECISION.md). Les étapes de comparaison architecturale A/B/C ou les verdicts 14/2 éventuellement mentionnés ci-dessous ne sont **plus** la feuille de route active. La production du noyau hybride est sur la branche `prototype/hybrid-kernel-v1`, non dans le lab ; les critères P3 physiques restent ouverts.

# Protocole de recherche — priorité à la meilleure abstraction

## Ordre obligatoire

**P0 — Périmètre figé.** SCOPE.md fixe responsabilités, frontières et planchers. Vérifier la complétude *avant* de rechercher une nouvelle abstraction. Aucun remplacement prématuré de la TCB.

**P1 — Baseline reproductible.** Recenser les propriétés effectivement démontrées sur `main@d6347dccec714c0193bbc43af5de7e96e3a9ad27`, les 18 constats, les reproductions et les dépendances externes. L'ancien code sert de corpus d'étude, jamais de contrat de compatibilité.

**P2 — Recherche adversariale systématique.** Construire une batterie indépendante d'attaques sur toutes les frontières de A et B : signatures, lois, quorums, temps, preuves, transition, obligations, réservation, crash, concurrence, egress, fournisseurs, reprise et déploiement. Chaque constat reçoit un scénario minimal falsifiable et un statut démontré/suspect/inconclusif.

**P3 — Inventaire puis analyse des causes racines ENSEMBLE.** Ne pas « fermer » une famille par une succession de patchs locaux. Grouper les symptômes par pertes de sens communes, rechercher des contre-exemples contradictoires et identifier les invariants réellement manquants. Remédier immédiatement par confinement/désactivation lorsqu'une faille exploitable l'exige, sans confondre mitigation et refonte.

**P4 — Recherche d'une abstraction plus simple.** Seulement une fois le scope complet et les causes suffisamment cartographiées, comparer plusieurs modèles : réduction de concepts, transitions contractuelles, preuves qualifiées, effet exact et obligations. Mesurer la complexité sémantique, la taille de la TCB *effective*, les dépendances communes et les coûts de preuve — pas seulement les lignes.

**P5 — Implémentation neuve et validations.** Zéro compatibilité exigée avec les formats ou API historiques. Tests de propriétés, reproductions adversariales, vérification indépendante, pannes injectées, contrats fournisseur réels, restauration et comparaison garantie par garantie.

**P6 — Itération jusqu'à convergence.** Rechercher de nouvelles attaques contre la nouvelle architecture. Une baisse du nombre de constats n'est pas, seule, une preuve ; suivre les causes racines nouvelles, les invariants couverts et les dépendances de confiance.

## Artefacts minimaux attendus

`GUARANTEE_MATRIX.md` ; `TRUST_BOUNDARIES.md` ; `THREAT_MODEL.md` ; `ATTACK_CATALOG.md` ; `ROOT_CAUSES.md` ; `ABSTRACTION_OPTIONS.md` ; `PROOF_PLAN.md`. Ces artefacts sont à produire par observation et expérience, jamais en recopiant les anciennes affirmations.

## Règles de validation

Une décision est exacte seulement relativement à ses entrées et hypothèses ; des données authentifiées peuvent être fausses. Toute preuve qui ouvre un droit doit être qualifiée selon son sujet et sa méthode. Toute sécurité prétendument « hors noyau » qui peut permettre un effet reste dans la revue de confiance. Une faille ouverte ne devient pas « résolue » parce qu'une documentation a été ajoutée.

**Aucun code de production vNext n'est autorisé à prétendre à une garantie supérieure sans démonstration correspondante.**

## Phase 3 — protocole vivant depuis campagne III

Pendant cette phase, appliquer [l'arbre empirique profondeur × couverture](EXPERIMENT_TREE_DEPTH_COVERAGE.md) et le [statut daté](findings/P3_LAB_STATUS.md). Toute affirmation doit distinguer observation, compréhension conditionnelle et hypothèse externe. Les résultats ne déterminent ni scope ni abstraction. Les priorités actuelles sont [campagne III](findings/P3_CAMPAIGN_III.md) et sa documentation des findings ; les étapes de conception décrites plus loin dans le protocole ne sont **pas ouvertes**.
