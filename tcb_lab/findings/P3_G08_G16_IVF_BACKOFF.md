# IV-F — Franchissement du backoff de 24 heures (G08/G16)

**9 octobre 2026.** Le [script IV-F](../experiments/p3_ivf_backoff.py) oppose cinq cycles espacés d'une minute à cinq cycles contenant un saut de **1500 minutes** au quatrième cycle. Deux résultats locaux sont observés pour chaque scénario : plans de maintenance, propositions déclarées, faits signés de `attempt:failed` avec leurs timestamps, et indicateurs `journal.health` `open/escalated/proven`.

**Hypothèse A :** l'inactivité après le retrait d'une réparation peut résulter de la condition `ATTEMPT_BACKOFF_MS = DAY` dans `ops/cycle.py`. **Hypothèse B :** le passage du délai ne suffit pas, faute de possibilité de réparation, d'état suffisamment frais ou de liveness/escalade. Le test peut départager certaines causes opérationnelles, mais ne garantit pas une progression.

**Attention :** une avance d'horloge de simulation doit être considérée avec les contraintes de fraîcheur/validité des témoins. Un refus `HIST.TIME` ou une exception de checkpoint rendrait le scénario `INCONCLUSIVE`, pas une violation G16. Un éventuel `open` dans le health doit être lié à la même cible et exigence avant d'établir G08.

**CI :** le workflow phase 3 est configuré pour lancer `p3_ivf_backoff.py`, valider `p3-ivf-backoff.json`, rejeter les sorties invalides, conserver les artefacts et publier la suite dans [issue #2](https://github.com/ichamafif-svg/NEW/issues/2). **Résultats non vérifiés au moment de la création de ce document.** Aucun changement du noyau, de la loi ou du scope. Les deux garanties demeurent `OPEN_SEMANTIC`.
