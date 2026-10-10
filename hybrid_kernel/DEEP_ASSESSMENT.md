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

`GovernedDeployment` exige une source de temps `trusted_now` et vérifie les neuf contrats T, l'attestation liée à la release, à la genèse, au journal et au registre, ainsi que l'absence de recul de l'horloge. Il revérifie lors des admissions et sous le verrou d'écriture, à la création de chaque token/réservation, et dans la garde juste avant l'envoi physique. Une expiration ou une indisponibilité à ce dernier point laisse la réservation ouverte à la réconciliation ; aucun effet n'est envoyé. L'état de santé est évalué au moins au temps courant de cette source.

Ce contrôle vaut uniquement si la source de temps, le registre, l'attestation et la garde sont installés hors de portée des agents. Les objets Python sont constructibles et les callbacks modifiables dans un processus qui exécute du code hostile : ils ne forment pas une frontière d'isolation. La façade ne transforme ni un inventaire `VERIFIED` auto-déclaré ni un `DeploymentAttestation` fabriqué localement en preuve de sécurité. Un opérateur doit mettre en place l'attestation authentifiée, les clés, le stockage indépendant, l'exclusivité réseau et la surveillance de cette frontière avant d'exposer des credentials privilégiés.

| Contrats | Mécanisme logiciel disponible | Condition physique restant à démontrer |
|---|---|---|
| T01–T03 | Pin de release/genèse, signatures, quorum logique, ancre historique et recontrôle temporel | Installation authentique, personnes distinctes, clés exclusives et horloge indépendante |
| T04–T05 | Journal ordonné, pin monotone, second contrôle AND et arrêt sur désaccord | Domaine de restauration et domaine de panne indépendants ; fencing multi-hôte |
| T06 | Méthode, source, sujet, couverture, fraîcheur et invalidation vérifiés par K | Vérité instrumentée, identité de la source et couverture effectivement mesurée |
| T07–T08 | Réservation avant départ, re-jugement, effet exact, UNKNOWN et réconciliation | Credentials et egress exclusifs, préconditions atomiques du fournisseur, déduplication et readback indépendants |
| T09 | Dette et condition d'escalade persistantes | Livraison, accusé, disponibilité et reprise du scheduler observés |

Ces points restent `UNVERIFIED_PHYSICAL` dans le manifeste de qualification. Des tests locaux de l'expiration et de la perte de confiance ne changent pas ce statut.

Un changement de release modifie les pins de code et de floors. Aucun état d'une autre release n'est accepté silencieusement ; une migration ou une nouvelle genèse relève du protocole de gouvernance externe applicable. Aucun reset automatique ni exception de bootstrap n'est fourni.
