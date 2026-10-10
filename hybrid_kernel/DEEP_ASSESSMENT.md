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

Un changement de release modifie les pins de code et de floors. Aucun état d'une autre release n'est accepté silencieusement ; une migration ou une nouvelle genèse relève du protocole de gouvernance externe applicable. Aucun reset automatique ni exception de bootstrap n'est fourni.
