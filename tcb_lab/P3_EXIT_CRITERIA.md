# Phase 3 — Critères de sortie bloquants (P3 HARD GATE)

**Décision de recherche : la phase 3 ne peut être clôturée par un nombre de scénarios, par un taux de tests verts, ni par une simple campagne CI.** Elle reste ouverte jusqu'à démonstration documentée de chaque condition. Les résultats négatifs restent conditionnels au modèle de menace. Ce gate n'autorise **aucun choix de nouvelle abstraction** avant consolidation des causes.

## Matrice obligatoire

Chaque garantie G01–G16 du laboratoire doit être évaluée suivant les cinq axes :

1. **Sémantique** — formes canoniques, décisions d'autorité, loi, temps, provenance, obligations, effets exacts.
2. **Compositions** — au moins deux responsabilités agissant dans des ordres opposés, et une séquence longue.
3. **Défaillances** — crash avant/après écriture durable, timeout fournisseur, restauration, réseau partitionné, quorum indisponible.
4. **Frontières physiques** — journal + pin, OS/crypto, secrets et rôle privilégié, fournisseur, déploiement et horloge.
5. **Autonomie** — scénario négatif bloqué ET scénario permis pouvant progresser ou ayant une raison explicite et observable de blocage.

Chaque cellule porte : `NOT_STARTED | TESTED_LOCAL | TESTED_MULTI_PROCESS | TESTED_EXTERNAL | NOT_APPLICABLE`, un identifiant d'essai, une observation brute et l'hypothèse indispensable. `NOT_APPLICABLE` exige une justification basée sur la garantie, pas l'absence de test.

## Portes de clôture

**P3-G1 — Inventaire vérifié :** toutes les garanties du scope, les chemins d'effet et les dépendances de confiance ont une ligne de couverture, y compris les sous-propriétés ajoutées par les attaques.

**P3-G2 — Reproductibilité :** toutes les attaques prioritaires ont un oracle explicite, des fixtures isolées, le commit et l'environnement, des logs vérifiés, un résultat honnête. Les résultats non exécutés restent visibles.

**P3-G3 — Profondeur d'interaction :** chaque responsabilité est éprouvée en interaction avec les autres auxquelles elle peut conférer une permission ou une clôture ; au moins une famille de séquences d'ordres opposés et de races sur les frontières critiques.

**P3-G4 — Défaillances physiques :** crash-injection avant/après pin, admission, réservation, départ, retour, preuve; tests multi-processus et multi-hôtes ou hypothèse d'exclusion explicite. Démonstration de l'absence d'egress alternatif sous le modèle de déploiement.

**P3-G5 — Preuves :** séparation authentification/vérité/qualification ; attaques sur univers complet, sujet exact, méthode, provenance commune, fraîcheur, fausse attestation et possibilité d'invalider.

**P3-G6 — Autonomie :** test de progression pour toute voie de réparation autorisée, refus sur chaque interdiction, dettes conservées et échéances stables pendant pannes et WorkItems ratés. Cas BUILD et RUN inclus sans mode god.

**P3-G7 — Revue contradictoire :** un autre modèle de test/oracle reproduit au moins les propriétés de haute criticité ; documentation des défauts partagés entre vérificateurs et de toutes les limites externes.

**P3-G8 — Exhaustion raisonnable :** après plusieurs campagnes distinctes sur les mêmes frontières, les nouveaux constats sont regroupés par causes racines ; toute faille critique ouverte est soit contenue, soit bloque le passage. Une absence absolue de nouvelles failles n'est jamais revendiquée.

## Livrables de clôture

`COVERAGE_DEPTH.md` (matrice vivante), `ATTACK_CATALOG.md`, `ATTACK_EXPANSION.md`, traces exécutées, `ROOT_CAUSE_CANDIDATES.md`, `EXTERNAL_ASSUMPTIONS.md`, `P3_EXIT_REVIEW.md`.

**État actuel : OUVERT** ; rien dans la branche ne vaut satisfaction automatique de ces portes.

## Mise en garde — recherche III

La campagne III cible les lacunes empiriques de la phase II mais n'atteint pas les niveaux D4–D7 physiques/distribués. Les critères de clôture restent **non remplis**, quelle que soit la couleur de la CI. Interpréter les rapports avec [l'arbre vivant](EXPERIMENT_TREE_DEPTH_COVERAGE.md) et [la synthèse empirique](findings/P3_LAB_STATUS.md), sans transformer les findings en architecture.

## IV-D — complément aux critères de sortie

La validation du scope fonctionnel requiert des réponses satisfaisantes pour G08 (obligation stable sous remplacement de proposition et changement de cible) et G16 (liveness conditionnelle, possibilité d'escalade sans agent souverain). Les scénarios [IV-D G08/G16](findings/P3_G08_G16_CAMPAIGN.md) sont exploratoires et ne suffisent pas, seuls, à la clôture.

## Décision de consolidation — 9 octobre 2026 (statut actuel du **découpage**)

La [décision canonique de frontière fonctionnelle](FUNCTIONAL_BOUNDARY_FREEZE_DECISION.md) attribue désormais **16/16 garanties G01–G16 à K (décisions du noyau), T (Trusted External) et U (autonomie remplaçable)** sous hypothèses explicites. **Statut : CONDITIONAL_BOUNDARY_FROZEN**, et **non** 16 garanties prouvées. Les anciennes mentions `14 conditionnelles / 2 ouvertes` ou `OPEN_SEMANTIC` pour G08/G16 décrivent **l'étape IV-C/IV-D historique** et sont supplantées **uniquement pour la délimitation fonctionnelle** ; elles restent utiles comme état des preuves à leur date. G08 : dette canonique indépendante des tentatives ; G16 : règles de permission, dette et exigibilité d'escalade dans K, scheduling/retries/notification dans U et préconditions fiables dans T. La campagne IV-I et les travaux d'implémentation ne bloquent **pas** la décision de découpage. Le scope sémantique `SCOPE.md` demeure intact ; l'assurance physique, l'audit de déploiement et les portes de sortie P3 restent **ouverts**. Ne pas relancer une boucle de recherche sur tout Standard sans contre-exemple démontrant une mauvaise attribution K/T/U.
