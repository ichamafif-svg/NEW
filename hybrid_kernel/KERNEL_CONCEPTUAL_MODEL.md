# Modèle conceptuel du noyau hybride

**Statut : modèle cible.** Le présent document définit le mécanisme conceptuel du noyau de Standard, indépendamment de tout dépôt, langage ou fournisseur. Voir [l'architecture produit](../STANDARD_ARCHITECTURE.md).

## Invariant central

**Un seul jugement constitutionnel** combine modèle relationnel typé, évaluation de contraintes finies, calcul de transitions et obligations persistantes. L'extensibilité porte sur les ressources et règles métier ; elle ne permet pas de redéfinir le sens de l'autorité, de la preuve, de la clôture et des effets.

Une fonction déterministe conceptuelle `judge(prefix, constitution, request, qualified_inputs) → decision` n'a aucun effet de bord. Sa décision lie le préfixe, les entrées canoniques et la version de la constitution ; elle produit un verdict, la raison, le delta nécessaire, les obligations et les autorisations exactes d'effets.

## Objets canoniques

| Objet | Définition | Invariant |
|---|---|---|
| Constitution | Release, floors et loi client composés | Le client ne peut pas affaiblir la release |
| Principal | Identité logique et provenance attestée | Plusieurs clés ne prouvent pas plusieurs humains |
| Resource | Identité stable et espace de noms | Aucun type métier privilégié codé en dur |
| Capability | Pouvoir lié à sujet, action, ressource et conditions | Délégation atténuante, révocation vérifiée |
| Claim / Evidence | Affirmation + qualification vérifiable | Signature ≠ véracité ou couverture |
| Obligation | Dette constitutionnelle liée à une exigence et un sujet | Retry ≠ nouvelle dette ou nouvelle échéance |
| Transition | Modification complète proposée et jugée | Aucun champ omis ou changement implicite |
| EffectIntent | Effet borné à destination, arguments et contexte | Autorisation logique ≠ départ physique |

Les relations constitutionnelles (détient, délègue, restreint, atteste, exige, clôture, autorise) sont typées et possèdent une signification fermée. Les relations métier additionnelles ne peuvent pas modifier cette signification.

## Ordre sémantique du jugement

1. Canonicaliser et borner les données ; authentifier la release et le préfixe.
2. Valider les déclarations et la chaîne d'autorité réelle, y compris restrictions, quorums, délais et témoins applicables.
3. Qualifier les preuves et la temporalité selon leur sujet, méthode, provenance, couverture, fraîcheur et indépendance.
4. Évaluer les floors et la loi client, les invariants et les contraintes applicables.
5. Dériver **toutes** les conséquences obligatoires : état, nouvelles dettes, clôtures autorisées, effet potentiel.
6. Refuser tout delta incomplet ou supplémentaire, émettre un résultat reproductible.

Le jugement n'exécute ni scanner, ni workflow, ni appel cloud. Les activités BUILD/RUN sont organisées par une couche autonome non souveraine.

## Cycles de vie

**Authority** : accord gouverné → usage borné → éventuelle atténuation → restriction/révocation/expiration. Un acteur isolé ne peut élargir les protections constitutionnelles ; les procédures de quorum, témoins et délais s'appliquent quand exigées.

**Evidence** : assertion → authentification → qualification indépendante et bornée → validité, insuffisance ou péremption. Une affirmation de succès de l'agent ne ferme aucune dette sans qualification.

**Obligation** : exigence insatisfaite → ouverture durable avec identifiant stable et échéance → tentatives multiples → preuve admissible → clôture ; à défaut, obligation persistante et éventuelle escalade due. Renommer un ticket n'efface pas une obligation.

**Effect** : intention → admission → commit → réservation → vérification à l'instant du départ → résultat confirmé ou incertain → réconciliation. Une révocation peut bloquer un départ non engagé, pas effacer un effet déjà appliqué.

## Invariants vérifiables

- Même préfixe canonique + mêmes entrées → même décision.
- Aucun acteur isolé ni composant isolé ne peut élargir la loi ou contourner les protections de la release.
- Une restriction applicable est opposable à tout départ d'effet concerné.
- Une preuve inadmissible ne clôt pas une obligation.
- Une dette non résolue persiste malgré les cycles d'agent et les changements de WorkItem.
- Toute transition possède un delta exhaustif, vérifié, atomique et auditable.
- Tout effet sensible passe par une garde effective, avec autorisation exacte et réserve durable.
- Toute décision dépendante d'une infrastructure de confiance indisponible échoue fermé.
- Une vérification indépendante requise ne se réduit pas à une signature supplémentaire du même acteur.

## Architecture de performance

Le jugement ne doit pas être invoqué pour chaque lecture, calcul ou tentative technique de l'agent. Des capacités limitées et vérifiables permettent l'autonomie opérationnelle. L'évaluation incrémentale des contraintes est possible uniquement si son équivalence avec le jugement canonique exhaustif est établie.

## Limite de la spécification

Les objets représentent les **contrats conceptuels**. Leur encodage exact, leur langage et leur topologie sont des décisions d'implémentation versionnées ; aucune de ces décisions ne peut affaiblir les invariants. La sécurité physique exige les [Trusted External](TRUSTED_EXTERNAL_CONTRACTS.md).
