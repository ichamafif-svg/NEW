# Protocole d'exécution constitutionnel de Standard

**Statut : protocole conceptuel cible ; implémentation et sûreté physique à valider.** Voir [architecture globale](../STANDARD_ARCHITECTURE.md), [modèle de K](KERNEL_CONCEPTUAL_MODEL.md) et [contrats T](TRUSTED_EXTERNAL_CONTRACTS.md).

## Contrat de bout en bout

L'autonomie BUILD/RUN propose des travaux ; la constitution décide des droits et des changements admissibles. Un effet sensible n'est exécuté que par une frontière privilégiée à laquelle l'agent n'accède pas directement.

`PROPOSED → AUTHENTICATED → JUDGED → COMMITTED → [NO_EFFECT | RESERVED → DISPATCHED → (CONFIRMED | UNKNOWN → RECONCILED)]`.

`REJECTED` et `PENDING_INPUT` sont des sorties sans mutation privilégiée. La décision d'escalader constitue une conséquence constitutionnelle ; la transmission physique se fait sous contrat de livraison.

## Phases normatives

| Phase | Responsable | Condition requise |
|---|---|---|
| 0. Préfixe valide | T01/T04 | Release, code, constitution, genèse, état et ancre authentiques |
| 1. Proposition | U | Requête canonique ; aucun pouvoir créé |
| 2. Qualification | T02/T03/T06 | Identité, preuve, temps et couverture vérifiables |
| 3. Jugement | K | Autorité réelle, loi, preuve, obligations et delta exhaustif |
| 4. Vérification | T05 selon contrat | Contrôle indépendant requis sans désaccord |
| 5. Commit | K/T04 | Préfixe attendu, transaction durable et anti-rollback |
| 6. Réservation | K/T07/T08 | Intention d'effet exacte et capacité bornée |
| 7. Départ | T07 | Egress exclusif, revalidation des restrictions, fencing, octets identiques |
| 8. Résultat | T08 | Résultat attesté ou `UNKNOWN` conservé |
| 9. Continuité | K/T09/U | Obligations conservées, clôtures prouvées, échéances/escalades suivies |

Les opérations non sensibles peuvent être absorbées par des capacités bornées pour ne pas refaire un jugement global à chaque action technique. Ces capacités n'accordent aucun pouvoir d'élargir la constitution.

## Cas de sûreté critiques

**Retry de réparation :** les tentatives/WorkItems peuvent changer, l'identité et l'échéance de la dette non résolue ne changent pas. Seule une preuve qualifiée autorise la clôture.

**Révocation concurrente :** le garde de départ voit l'état et les restrictions applicables, avec ordre et fencing conformes à la loi. Une décision précédente ne permet pas de partir après révocation applicable.

**Timeout fournisseur :** une réservation existe avant l'appel ; si le fournisseur a pu être atteint, `UNKNOWN` ne signifie jamais `not_applied`. Réconciliation ou idempotence effectivement démontrée avant un nouvel envoi.

**Reprise après restauration :** la reprise vérifie une ancre indépendante et la continuité du préfixe ; tout rollback détecté bloque les effets.

**Changement constitutionnel :** la loi client ajoute ou durcit seulement ; élargissement, dégel et changement des racines suivent leur procédure de gouvernance et les délais/témoins applicables. Aucune procédure de bootstrap ne devient god mode.

## Objets d'interface conceptuels

- `SignedRequest` : domaine, sujet, opération, ressource, id, empreinte de préfixe, intention canonique et signatures.
- `QualifiedEvidence` : exigence, sujet, méthode, mesure, couverture, origine, temps et validation indépendante.
- `Judgment` : version, verdict, raison, préfixe, delta obligatoire, conséquences d'obligations, effet potentiel et trace vérifiable.
- `CommitReceipt` : préfixes ancien/nouveau, numéro logique, ancre indépendante et attestation éventuelle du vérificateur.
- `EffectGrant` : ressource, destination, action, empreinte exacte d'arguments, durée, autorité et réservation.
- `EffectReceipt` : tentative, fournisseur, résultat, provenance, observation ou incertitude, corrélation à la réservation.

Ces interfaces sont conceptuelles ; leur schéma exact doit être fermé et versionné avant déploiement.

## Critères de mise en service

Aucun chemin alternatif ne doit pouvoir signer une autorisation, modifier le ledger ou sortir un effet privilégié. Les défaillances et désaccords critiques échouent fermé. Les garanties de progression restent assorties de conditions mesurables de disponibilité et d'équité. Une qualification exige tests adversariaux, preuves indépendantes, reprise sur panne et mesures de performance.
