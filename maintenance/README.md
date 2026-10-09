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

Cette projection générique est présente, mais le cycle opérationnel M2 utilise encore `ops/lifecycle.py` et ses cibles de floors statiques. L'unification de leurs obligations/routes et des cibles client effectives reste une cible de [COEUR-STABLE.md](../docs/COEUR-STABLE.md), pas une propriété implémentée.
