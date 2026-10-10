# Noyau constitutionnel hybride — état d'implémentation

**Un jugement constitutionnel implémenté ; production bloquée dans l'attente de qualification indépendante des Trusted Externals.**

Le chemin unique est `hybrid_kernel.core.Kernel.decide` → contrôle indépendant → journal ancré. `Kernel.judgment` expose le même jugement sous forme immuable ; son delta est entièrement redérivé avant une réduction en mémoire. Cette réduction ne remplace pas le commit durable. `ConstitutionalRuntime` et `SQLiteAdmission` utilisent le même journal, les mêmes pins et les mêmes contrôles. Aucun reçu `allowed` n'est une source d'autorité.

## Réalisation

| Responsabilité | Implémentation |
|---|---|
| Identités, quorum, témoins, délais, veto, rotation et activation | `core.py`, primitives cryptographiques et FLOOR-0 épinglées |
| Constitution additive, floors et schémas gouvernés | `constitution.py` |
| Autorité atténuante, gel, révocation, budgets de chaîne | `core.py` |
| Relations typées, contraintes positives bornées | `model.py`, `relations.py` |
| Ressources et transitions finies, conséquence exhaustive | `core.py`, `model.py` |
| Mesures qualifiées, méthode, couverture, fraîcheur et invalidation | `core.py`, `model.py` |
| Obligations linéaires, dette stable et escalade | `obligations.py`, `debt.py` |
| Effets exacts, réservation, revalidation, UNKNOWN et réconciliation | `core.py`, journal et garde T |
| Contrôle AND indépendant des conséquences | contrôle d'intégrité, `checker.py` |

Les imports de compatibilité ne contiennent aucune autre implémentation. Les deux espaces de noms, tous les composants T et tous les contrôles indépendants sont comptés par `tools/check_tcb.py`. Le budget K de 1 800 à 3 200 lignes inclut les primitives réutilisées et la sémantique déterministe de dette ; il exclut les mécanismes physiques T et le contrôle AND, qui restent explicitement comptés dans la TCB effective.

## Qualification

`make check` exécute le budget, les suites constitutionnelles, les tests d'intégration, les transitions relationnelles, les preuves instrumentées et la persistance des dettes. Le laboratoire adversarial distingue refus, observations et limites physiques ; une observation n'est pas automatiquement un défaut de K.

Les signatures ne prouvent ni la vérité d'une mesure ni la séparation physique des humains. Le stockage local ne prouve pas l'indépendance des domaines de restauration. Le contrôle AND n'établit pas à lui seul l'indépendance des domaines de panne. L'exclusivité des credentials, le fencing entre hôtes et la livraison des escalades doivent être qualifiés sur le déploiement réel.

### Durée de validité des contrats T

`GovernedDeployment` reçoit une frontière `TrustBoundary.check(required, release_digest, genesis_pin, ledger_path, now)` choisie par l'installation. Les neuf T sont des responsabilités regroupables, pas neuf processus ni une attestation globale obligatoire. La frontière qualifie seulement les rôles utilisés par l'opération : T01/T02/T04/T05 pour le préfixe et les restrictions signées, T03 en plus pour les opérations temporelles, T06 pour une observation, une mesure ou une preuve déclarée par la loi, T08 pour une réconciliation, T07/T08 pour les étapes d'effet et la garde, et T09 uniquement pour la livraison. Une panne T09 n'empêche pas une admission ordinaire ; une panne T03 n'empêche pas un gel ou une révocation signés. En revanche, aucune opération dépendante ne progresse sans son contrat. Les contrôles sont répétés sous le verrou du journal ou de la garde juste avant le départ physique. Une perte de confiance à ce dernier point laisse la réservation à réconcilier sans envoyer l'effet. `trusted_now` est consulté sur les voies temporelles, détecte le recul et borne l'évaluation de santé.

`assessment.py` est un adaptateur possible : `SignedAssessmentBoundary` authentifie une évaluation Ed25519 partielle ou complète, ses dates et son lien à la release, la genèse, le journal et le registre. Lors d'une restriction sans temps fiable, il contrôle l'évaluation à sa date d'émission signée, sans prétendre qu'elle est encore fraîche ; cette voie ne peut pas élargir l'autorité. Les clés de l'évaluateur doivent être épinglées par l'installation. Une déclaration `VERIFIED` et une signature ne démontrent pas la réalité physique du contrat. Les objets Python et callbacks restent modifiables dans un processus exécutant du code hostile : la frontière doit être installée hors de portée de U, avec stockage et credentials isolés, avant tout départ privilégié. La garde reçoit son port d'effet lors de l'installation ; l'appelant d'une opération ne peut pas fournir un nouveau handler dans `GovernedDeployment`.

`delivery.py` est un adaptateur logiciel possible de T09 : une notification d'escalade est mise en outbox durable sous une clé stable d'obligation, puis marquée *tentée* avant l'envoi. Une réponse perdue ne provoque pas un deuxième envoi ; le transport doit fournir un readback et un reçu signé qui lie la clé, le payload et les destinataires. Sans reçu recevable, le statut reste inconnu. Un crash après la marque *tentée* mais avant l'envoi exige une réconciliation externe. Un `delivery_port` provisionné peut être appelé par `GovernedDeployment.deliver_due` avec la santé du journal ; son absence n'arrête que cette voie. La signature du fournisseur ne prouve pas à elle seule qu'une personne a effectivement reçu l'alerte.

`clock.py` est un adaptateur possible de T03 : un défi aléatoire neuf, au moins deux témoins avec clés distinctes, signatures sur le domaine et la genèse, accord temporel exact et refus du recul. Le noyau consomme un timestamp entier ; cet adaptateur refuse donc une incertitude non nulle. D'autres fournisseurs peuvent satisfaire le contrat s'ils prouvent les bornes temporelles requises. Leur indépendance reste à qualifier physiquement.

| Contrats | Mécanisme logiciel disponible | Condition physique restant à démontrer |
|---|---|---|
| T01–T03 | Pin de release/genèse, évaluation T signée, signatures, quorum logique, ancre historique, défi frais et horloge cosignée | Clés d'évaluateur/témoins épinglées hors de l'agent, installation authentique, personnes distinctes et horloge indépendante |
| T04–T05 | Journal ordonné, pin monotone, second contrôle AND et arrêt sur désaccord | Domaine de restauration et domaine de panne indépendants ; fencing multi-hôte |
| T06 | Méthode, source, sujet, couverture, fraîcheur et invalidation vérifiés par K | Vérité instrumentée, identité de la source et couverture effectivement mesurée |
| T07–T08 | Réservation avant départ, re-jugement, effet exact, UNKNOWN et réconciliation | Credentials et egress exclusifs, préconditions atomiques du fournisseur, déduplication et readback indépendants |
| T09 | Dette persistante, outbox avant envoi, lecture de retour et reçu signé | Vérité du readback et des destinataires, disponibilité, reprise du scheduler et accusé humain observés |

Ces points restent `UNVERIFIED_PHYSICAL` dans le manifeste de qualification. Des tests locaux de l'expiration et de la perte de confiance ne changent pas ce statut.

Un changement de release modifie les pins de code et de floors. Aucun état d'une autre release n'est accepté silencieusement ; une migration ou une nouvelle genèse relève du protocole de gouvernance externe applicable. Aucun reset automatique ni exception de bootstrap n'est fourni.
