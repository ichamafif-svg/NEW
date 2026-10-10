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

`GovernedDeployment` exige une source de temps `trusted_now` et une évaluation T01–T09 signée en Ed25519 par un évaluateur dont la clé publique est épinglée par l'installation. `assessment.py` vérifie la signature, les neuf contrats, leurs dates et le lien exact avec la release, la genèse, le journal et le registre. Les anciens objets `registry` et `deployment_attestation` construits localement sont refusés par cette façade. Elle revérifie la validité des contrats et l'absence de recul de l'horloge lors des admissions et sous le verrou d'écriture, à la création de chaque token/réservation, et dans la garde juste avant l'envoi physique. Une expiration ou une indisponibilité à ce dernier point laisse la réservation ouverte à la réconciliation ; aucun effet n'est envoyé. L'état de santé est évalué au moins au temps courant de cette source.

Ce contrôle vaut uniquement si la source de temps, les clés publiques de l'évaluateur, le registre, l'attestation et la garde sont installés hors de portée des agents. Passer au constructeur une clé publique choisie par l'appelant permettrait de signer soi-même une fausse évaluation. Les objets Python et les callbacks restent modifiables dans un processus qui exécute du code hostile : ils ne forment pas une frontière d'isolation. L'opérateur doit ancrer les clés et le code dans une installation contrôlée, isoler les credentials, le stockage et l'egress, puis mesurer ces propriétés avant tout départ privilégié.

`delivery.py` implémente la partie logicielle de T09 : une notification d'escalade est mise en outbox durable sous une clé stable d'obligation, puis marquée *tentée* avant l'envoi. Une réponse perdue ne provoque pas un deuxième envoi ; le transport doit fournir un readback et un reçu signé qui lie la clé, le payload et les destinataires. Sans reçu recevable, le statut reste inconnu. Un crash après la marque *tentée* mais avant l'envoi exige une réconciliation externe ; la sûreté prime sur une relance aveugle. `GovernedDeployment.outbox` lie cette outbox à la santé authentifiée du journal et au contrôle de confiance courant. La signature du fournisseur ne prouve pas à elle seule qu'une personne a effectivement reçu l'alerte : cette propriété reste à qualifier avec le fournisseur et l'accusé de réception.

`clock.py` fournit une source `trusted_now` concrète pour T03 : un défi aléatoire neuf, au moins deux témoins avec clés distinctes, signatures sur le domaine et la genèse, accord temporel exact et refus du recul. Le noyau actuel consomme un timestamp entier ; autoriser un intervalle d'incertitude non nul sans utiliser sa borne basse pour les délais et sa borne haute pour les expirations pourrait accorder des droits. Le port refuse donc une incertitude non nulle. Les témoins, leurs clés, leur transport et leur indépendance restent à installer et qualifier physiquement.

| Contrats | Mécanisme logiciel disponible | Condition physique restant à démontrer |
|---|---|---|
| T01–T03 | Pin de release/genèse, évaluation T signée, signatures, quorum logique, ancre historique, défi frais et horloge cosignée | Clés d'évaluateur/témoins épinglées hors de l'agent, installation authentique, personnes distinctes et horloge indépendante |
| T04–T05 | Journal ordonné, pin monotone, second contrôle AND et arrêt sur désaccord | Domaine de restauration et domaine de panne indépendants ; fencing multi-hôte |
| T06 | Méthode, source, sujet, couverture, fraîcheur et invalidation vérifiés par K | Vérité instrumentée, identité de la source et couverture effectivement mesurée |
| T07–T08 | Réservation avant départ, re-jugement, effet exact, UNKNOWN et réconciliation | Credentials et egress exclusifs, préconditions atomiques du fournisseur, déduplication et readback indépendants |
| T09 | Dette persistante, outbox avant envoi, lecture de retour et reçu signé | Vérité du readback et des destinataires, disponibilité, reprise du scheduler et accusé humain observés |

Ces points restent `UNVERIFIED_PHYSICAL` dans le manifeste de qualification. Des tests locaux de l'expiration et de la perte de confiance ne changent pas ce statut.

Un changement de release modifie les pins de code et de floors. Aucun état d'une autre release n'est accepté silencieusement ; une migration ou une nouvelle genèse relève du protocole de gouvernance externe applicable. Aucun reset automatique ni exception de bootstrap n'est fourni.
