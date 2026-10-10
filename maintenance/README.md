# Travail proposé à partir d'un audit

Cette couche hors TCB transforme une vue `health()` en propositions de travail. Elle ne vérifie pas cryptographiquement son entrée : fournir la sortie de l'auditeur épinglé, garder la vue originale visible et rejuger toute intention ultérieure.

```sh
python3 -m maintenance < health.json > work-plan.json
```

- `WORK` : écarts de cibles avec besoins de couverture, observation, réparation ou preuve.
- `REVIEW` : présence de travail escaladé ou d'une obligation de protocole demandant une revue. Du travail sur les cibles peut aussi rester proposé.
- `IDLE` : aucun travail dans cette vue ; aucune certification ni garantie de santé hors des cibles déclarées.
- `BLOCKED` : audit en faute, historique explicitement dépassé ou structure incohérente. Aucune proposition n'est émise ; le CLI retourne 1.

L'identifiant d'obligation et l'échéance sont conservés. Le plan nomme la tête et l'horizon de l'audit ; il ne reste pas automatiquement actuel après une écriture. Il ne transmet aucune permission, n'envoie aucune notification, n'exécute aucun agent et ne signe aucune entrée. Une étape « réparer » est une proposition à préparer sous la loi en vigueur, pas un appel de fournisseur. Les besoins inconnus restent bloqués plutôt qu'interprétés.

Cette projection générique est présente, mais le cycle opérationnel M2 utilise encore `ops/lifecycle.py`. Les sondes M2 connues lisent désormais les cibles effectives, y compris les resserrements clients ; les obligations, routes et nouvelles cibles métier ne sont pas encore unifiées dans un moteur de travail commun. Ce reste à faire est décrit dans [COEUR-STABLE.md](../docs/COEUR-STABLE.md).

`maintenance.constitution.agent_view` expose séparément la loi effective
authentifiée par le noyau au préfixe exact du rapport, les propositions de
travail et les contrats T encore non qualifiés dans le manifeste de release.
Le rapport du demo écrit une vue lisible dans `constitution.md` ; le modèle de préparation
des réparations non déterministes reçoit une vue ciblée de sa seule exigence.
La structure interne reste disponible au service de projection. Ces écarts T sont des
indices de qualification de release, sans statut d'obligation constitutionnelle
ou de mesure du fournisseur en direct. `trust_work` propose l'implémentation et
la collecte de preuves, dont la clôture exige une qualification indépendante ;
le cycle M2 ne l'ordonnance pas encore. La vue ne contient aucun grant exécutable.
