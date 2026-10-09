# Standard TCB — V7

V7 = la V6 (fusion de V0 et de la V5) corrigée par cause racine après revue adversariale :
polarité typée, automate unique du cycle d'effet, identité sur le sens signé, faits étiquetés.
Détail, attaques et vérifications : [docs/REVUE-V6.md](docs/REVUE-V6.md).

Cette V6 conserve les protections de la V0, reprend les lois en couches et la redevabilité injectée de V5,
et corrige les scénarios adversariaux reproduits dans les deux bases. Le bilan détaillé est dans
[ANALYSE-V6.md](docs/ANALYSE-V6.md), les frontières dans [TCB.md](docs/TCB.md).

Le prototype est fonctionnel. `make test` vérifie les comportements ; `make check` vérifie aussi trois budgets,
chacun nommé par la garantie qu'il porte : **sûreté** (plafond historique de 2 942 lignes), **restrictif seul**
(le second juge, joint par ET) et **visibilité** (la redevabilité). Chaque ligne de confiance est comptée une fois.
Le classement est justifié par une structure vérifiée (importateurs autorisés, `tests/test_budget_classification.py`).
Aucun ancien journal ou ancienne genèse ne doit être réutilisé avec cette release. Aucun client de production
n'est présumé ; la compatibilité héritée ne gouverne pas les choix.

La vision produit et les choix conservés sont dans [docs/VISION.md](docs/VISION.md).
Le jalon M2 (maintenance autonome, sûre et conforme : `ops/`, `compliance/`, `adapters/`, `demo/`) est décrit dans
[docs/M2.md](docs/M2.md).
La projection du travail, sans autorité, est décrite dans [maintenance/README.md](maintenance/README.md).

## Organisation

| Emplacement | Contenu |
|---|---|
| `tcb/` | Code du cœur, sans documentation ni tests |
| `maintenance/` | Propositions de travail hors TCB, en lecture seule |
| `tests/` | Tests et fixture commune |
| `tools/` | Contrôle du budget et génération du manifeste |
| `docs/` | Analyse V6, garanties et corrections |
| `validation/` | Résumé JSON, résultats des tests, budget et mesures exploratoires |
| `bootstrap.py` | Entrée de confiance avant import du cœur |
| `tcb-budget.json` | Périmètre compté et plafond de lignes |
| `tcb-release.json` | Manifeste des sources et du runtime |

Les commandes se lancent depuis ce dossier. Les deux fichiers de contrôle restent à la racine, près du bootstrap.
Le bilan est dans [validation/summary.json](validation/summary.json).

## Entrées et conditions

La genèse apporte une loi `standard-client/1` liée au digest des floors de la release. `compose` ajoute les floors,
lie leurs rôles aux identités client et accepte seulement les resserrements déclarés. La loi effective utilise
`standard-v0/1`, le langage fini intégré. Une condition est une conjonction de 1 à 16 prédicats parmi `eq`, `prefix`,
`observed`, `closed_at_least`, `open`. Aucun Datalog, code inline, glob, négation, jointure ou récursion.

Une capacité ne porte que des noms scellés et épingle leur contenu. Les faits utilisés pour agir sont frais et
issus de chaînes sans détenteur commun avec l'acteur. Les clôtures propres ne donnent pas d'autonomie.
Les OBL conservent les niveaux `refuse`, `escalate`, `measure`.

Une opération déclare `args`, `resource`, `profile`. Les profils sont `capability` et `human_quorum`. Le client peut
renforcer une opération des floors via `tighten.ops`, sans changer ses arguments ni sa ressource. L'acteur ne
choisit jamais le profil. Un template de ressource comporte au plus un paramètre par segment, éventuellement
avec préfixe et suffixe littéraux ; les arguments répétés doivent avoir la même valeur. Le contrôle des routes de
réparation inverse ce template typé sans expressions régulières avec jokers ni recherche combinatoire.

## Effets et redevabilité

Réservation durable et épinglée, recontrôle par les deux juges, comparaison exacte des effets, puis envoi physique
sous le verrou. Un adaptateur peut renvoyer une fonction qui attend le résultat d'une demande déjà envoyée ;
cette attente a lieu hors du verrou. Les adaptateurs restent de confiance. Leur attente ne peut pas envoyer
une autre demande. Après entrée fournisseur, une exception reste `unknown` et exige une réconciliation.

Le magasin `SQLitePins` doit appartenir à un domaine de restauration indépendant. Une épingle en avance après
un crash bloque les opérations ; `recover_tail` restaure l'entrée signée exacte, sans baisser l'épingle.
Le fournisseur reçoit `(resource, args, reservation_key)`. La déduplication distante dépend de lui.

L'auditeur confiné est persistant et incrémental. `health()` exige un verdict actuel à sa frontière de contrôle ;
`health(prefix=True)` permet explicitement un verdict historique étiqueté. `required_at` expose l'expiration des
preuves sans avancée du journal. L'auditeur ne peut accorder aucun droit.

## Exécution

Python, cryptography et Linux/libseccomp sont nécessaires. Le manifeste sélectionne les sources locales et
l'identité du runtime, sans prouver l'intégrité binaire du runtime ou du système.

```sh
python3 -m pip install -r requirements.txt
make test
make check
make manifest
python3 -I -B bootstrap.py DIGEST_APPROUVE --verify
python3 -I -B bootstrap.py DIGEST_APPROUVE --health configuration.json
```

La configuration health nomme `journal`, `pins`, `genesis_pin`, éventuellement `required_at`.
Le digest de code approuvé et la genèse attendue doivent être conservés extérieurement.
Générer un manifeste ne l'approuve pas. Le bootstrap et les sources doivent être installés et protégés.
Cette livraison n'inclut ni agent de maintenance, ni adaptateur GitHub/GitLab, ni preuve formelle.
