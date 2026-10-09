# Phase 3 — Deuxième vague : résultats empiriques et limites

**Run de référence [#67](https://github.com/ichamafif-svg/NEW/actions/runs/37953587803)**, job adversarial `113898339669`. Les trois scripts ont terminé avec exit code zéro. Les logs ont été inspectés directement. Les sorties O1 incluaient des messages non-JSON du simulateur ; le registre les a donc signalées `INVALID_JSON` malgré l'exécution réussie ; la correction du harnais est soumise sur les commits ultérieurs et doit être vérifiée sur un run récent.

## P1 — 7 comparaisons d'attestations signées

Le signer `readback` muni de l'autorisation attendue a fait admettre un sujet exact avec drapeau externe `truth=False` ; ce drapeau est intentionnellement **absent** de l'entrée signée et ne peut être jugé par le noyau. Le contre-exemple observable est une attestation **syntaxiquement et cryptographiquement valide, mais fausse selon la fixture** qui peut fermer la dette de preuve. Les essais auteur `agent` et sujet `repo:pr:43` ont obtenu des refus. Le niveau `unknown` et le timestamp très décalé sont des contrastes mesurés mais ne prouvent ni une politique de fraîcheur adéquate ni une validation indépendante de la méthode.

**À approfondir :** provenance de l'oracle, source physique commune, couverture exacte du scan, empreinte du code observé, fraîcheur spécifique de la preuve. Ne pas conclure que « le noyau accepte toutes les preuves fausses » : seule une catégorie de preuve mensongère dont l'autorité signataire est reconnue est observée.

## E1 — 8 contrastes d'exécution + second journal

Les résultats `ack_lost`, `unknown`, `ok`, `failed` ont été essayés avec un deuxième redeem sur le même guard et sur un guard obtenu par `other_journal()`. Dans le log consulté, `ack_lost-other_journal` montrait **un seul appel au port** et le deuxième redeem refusé `HIST.TIME`. Le fait que le deuxième appel n'atteigne pas le port dans cette fixture reste distinct d'une garantie d'idempotence sur un fournisseur réel. Le code d'erreur `HIST.TIME` est un indice de précondition temporelle, **pas** une preuve indépendante que le fencing fonctionnerait sous crash/partition.

**À approfondir :** réessayer avec temps réaligné et horloge valide, injecter crash après envoi et avant écriture d'ACK, mesurer le nombre d'effets physiques avec provider controllable, et prouver l'absence de chemin de sortie hors guard.

## O1/R1 — 16 répétitions au même code

Les essais instrumentent dix variantes identiques `found:1` sur deux cycles, trois variantes `found:1` sur trois cycles et trois témoins `none`. Les runs montrent les phases et le booléen `historic_assertions_hold`. Cette collecte **ne démontre pas encore** la causalité de l'ancien échec historique : le harnais utilisé produit des simulations fraîches, avec identités/commits synthétiques différents. Les observations des scénarios ont été imprimées dans les logs, mais le rapport JSON était invalide à cause de sorties de simulateur ; une correction d'instrumentation est en cours.

**À approfondir :** comparer ancien SHA rouge/vert, exécuter un stress au **même commit avec mêmes seeds et mêmes préconditions**, capter états complets et obligations d'une **même cible** plutôt que comparer uniquement les phases.

## Signaux de mesure (à ne pas masquer)

Le job vert ne suffit pas pour conclure à une expérience correctement enregistrée. L'[issue #2](https://github.com/ichamafif-svg/NEW/issues/2) signalait explicitement `INVALID_JSON` pour les deux variantes O1 : ces sous-rapports ne peuvent pas compter comme couverture avec trace JSON reproductible tant que leur nouveau run n'est pas vérifié.

Les trois priorités et tous les axes du [backlog de couverture](P3_DEPTH_COVERAGE_BACKLOG.md) restent ouverts. Les résultats sont utilisés pour fabriquer les **prochaines expériences plus profondes**, jamais pour présélectionner une abstraction.
