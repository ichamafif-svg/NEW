# Plan directeur du laboratoire — Standard TCB

**Référence immuable d'analyse :** `main@d6347dccec714c0193bbc43af5de7e96e3a9ad27` ; **scope figé** : [SCOPE.md](SCOPE.md). **Mandat :** recherche TCB uniquement, sans chantier d'agent ni M2. Aucune compatibilité d'implémentation exigée ; aucune baisse silencieuse de garanties.

## Programme et portes

| Phase | Activité et livrable | Sortie vérifiable | État au démarrage phase 3 |
|---|---|---|---|
| 1 | Référence de sécurité : inventaire FLOOR-0, garanties, contrôles, hypothèses ; [GUARANTEE_MATRIX.md](GUARANTEE_MATRIX.md) | Chaque garantie possède propriétaire de décision, d'application et preuve attendue | Démarrée, matrice initiale de 16 familles, **non exhaustive** |
| 2 | Complétude du scope : frontières logiques et physiques, credentials, concurrence, crash, provenance ; [THREAT_MODEL.md](THREAT_MODEL.md) | Aucun pouvoir implicite hors frontière ; inconnues visibles | Démarrée, **non démontrée** |
| 3 | Campagnes adversariales : scénarios, reproductions isolées, oracle d'observation, résultats ; [ATTACK_CATALOG.md](ATTACK_CATALOG.md), `experiments/` | Chaque constat reproductible et marqué par niveau de certitude | **EN COURS** |
| 4 | Regroupement par cause racine et contre-exemples ; `ROOT_CAUSES.md` | Familles expliquées par des invariants manquants plutôt que patches individuels | Non commencée |
| 5 | Comparaison sans préférence préalable entre abstractions | Plusieurs modèles, impossibilités, coût de vérification et dépendances | Bloquée jusqu'au matériau phases 1–4 |
| 6 | Prototypes TCB concurrents, sur même corpus | Mesures falsifiables et non-régression | Non commencée |
| 7 | Noyau neuf et infrastructure de confiance | Garanties comparées une par une et preuves de déploiement | Non commencée |
| 8 | Nouvelle campagne contre le noyau candidat | Familles anciennes et nouvelles soumises aux mêmes contraintes | Non commencée |

## Discipline des constats

Chaque attaque reçoit : un identifiant stable, une garantie ciblée, une capacité d'attaquant explicite, une précondition, une procédure, un oracle falsifiable, les résultats (avec environnement/commit), les contournements de validation, les hypothèses externes, un statut et une piste de cause racine **non résolue**. Utiliser : `NOT_RUN`, `CONFIRMED`, `REFUTED_UNDER_ASSUMPTIONS`, `INCONCLUSIVE`, `BLOCKED`. Un test écrit ne donne pas le statut CONFIRMED. Une violation sur un mock ne démontre pas une exploitation du fournisseur.

**La phase 3 peut commencer pendant que les phases 1 et 2 sont incomplètes**, à condition de mettre à jour ces dernières quand une attaque révèle une frontière ou une propriété oubliée. Pas de nouvelle abstraction centrale au cours de cette phase.

## Préserver les garanties

Distinguer `SIGNATURE_VALID`, `ASSERTION_TRUE`, `EFFECT_APPLIED` et `REQUIREMENT_SATISFIED`. Distinguer verrou local, exclusivité inter-hôtes et exclusivité fournisseur. Distinguer compatibilité de tests et preuve indépendante. Aucune attaque destructive sur une ressource réelle : les expériences doivent utiliser des fixtures, doubles explicites ou répertoires isolés.
