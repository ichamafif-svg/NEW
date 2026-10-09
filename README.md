# Standard — cœur déterministe et maintenance M2

Standard est un prototype de maintenance gouvernée de dépôts. Les agents préparent des changements ; un cœur déterministe vérifie la loi, les capacités, les restrictions et les faits signés. Un guard réserve et rejuge l'effet avant l'appel fournisseur. La preuve d'application et la satisfaction de la cible restent distinctes.

La version active reprend la refonte M2 du tour 2 : **transitions `base → head`, recettes reproductibles, instruments séparés, revue du SHA exact et retrait des propositions rejetées**. Elle n'utilise plus les PR et leur scope de fichiers pour autoriser `remediate`.

## Fonctionnement présent

| Surface | Implémentation |
|---|---|
| Loi | FLOOR-0, floors communs, loi client additive ou plus stricte ; quorum, délai attesté et activation |
| Cœur | Admission pure, delta, second juge restrictif, journal signé et pins monotones |
| Effet M2 | `remediate(area,item,base,head)` ; ressource `repo:{area}:{item}/{base}/{head}` |
| Autonomie | Faits indépendants `tests=green` et `reproduced=yes` ; sinon `tests=green` et revue humaine signée |
| Préparation | Recettes pour vulnérabilités, SBOM et actions ; modèle pour changements nécessitant du jugement |
| Intégrations | API d'objets Git, adaptateur de fast-forward GitHub, sondes Python, runner de tests |
| Travail | Automate des propositions dans `ops/lifecycle.py` ; projection de santé en lecture seule dans `maintenance/` |
| Conformité | Catalogue ISO 27001/NIS2/DORA et dossier rejouable ; projection de preuves, sans certification |

L'adaptateur réel est présent dans les sources. Le service géré, son déploiement et les garanties fournisseur ne sont pas établis par les tests locaux. Le second juge ne couvre pas indépendamment toute la loi. Les limites de temps, de preuves, de reprise et de credentials restent détaillées dans [TCB.md](docs/TCB.md) et [M2.md](docs/M2.md).

## Lire le dépôt

- [Statut canonique et frontières](docs/STATUS.md).
- [État actuel et commandes M2](docs/M2.md).
- [Garanties et frontières du cœur](docs/TCB.md).
- [Vision produit](docs/VISION.md).
- [Cible de stabilisation en cinq contrats](docs/COEUR-STABLE.md), encore partiellement réalisée.
- [Historique de consolidation et reprise de la refonte](docs/CONSOLIDATION-BRANCHES.md).
- [Validation actuelle](validation/summary.json) ; analyses V6 et reproductions historiques séparées.

| Répertoire | Responsabilité |
|---|---|
| `tcb/`, `bootstrap.py` | Admission, intégrité, effet et redevabilité confinée |
| `adapters/` | Adaptateurs de confiance, comptés dans le budget de sûreté |
| `ops/` | Collecte, mesure, recettes, préparation, cycle et lancement des rôles |
| `maintenance/` | Plan sans pouvoir d'autoriser, de signer ou d'exécuter |
| `compliance/` | Catalogue et dossier projeté depuis le journal |
| `demo/` | Dépôt volontairement imparfait et workflow de démonstration |
| `tests/` | Scénarios du cœur et du cycle M2 |
| `validation/` | Résultats actuels et archives de revue |

## Vérifier localement

Python, cryptography et Linux/libseccomp sont nécessaires pour les vérifications complètes.

```sh
python3 -m pip install -r requirements.txt
make check
make manifest
python3 -I -B bootstrap.py DIGEST_APPROUVE --verify
python3 -I -B bootstrap.py DIGEST_APPROUVE --health configuration.json
```

Le manifeste dépend du runtime et des sources ; le générer ne l'approuve pas. Le digest et la genèse attendue doivent être sélectionnés extérieurement. Le bootstrap couvre la vérification et la santé ; les commandes `python -m ops` sont encore un chemin opérationnel distinct, pas un launcher vérifié avant import.

La refonte change les floors et les arguments de `remediate` : **nouvelle release adoptée et nouvelle genèse requises**. Les journaux et capacités de la précédente opération PR ne sont pas réutilisables. BUILD et RUN restent une vision de produit ; il n'existe pas encore deux modes complets de service gouverné.

Les budgets restent 2 942 lignes de sûreté, 537 restrictives et 500 de visibilité. Leur mesure actuelle vient de `tools/check_tcb.py`, sans compaction ni transfert artificiel hors confiance.
