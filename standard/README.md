# Surface commune BUILD/RUN

`StandardService` projette les obligations du noyau sur des tâches stables à partir
d'un `GovernedDeployment` installé et de routes déclarées par l'opérateur. Une
route décrit le mode, le sujet, le besoin et les contrats T nécessaires. Le
service contrôle leur disponibilité en direct et conserve les trous visibles.

```python
from standard import Route, StandardService

service = StandardService(deployment, [
    Route("repo-observe", "BOTH", "repo:*",
          frozenset({"cover", "observe"}), frozenset({"T06"})),
    Route("repo-build", "BUILD", "repo:*",
          frozenset({"build"}), frozenset({"T06"})),
])
cycle = service.inspect(mode="RUN")
```

`WorkEngine("work.sqlite3", service)` synchronise cette vue et loue les tâches
`READY` aux travailleurs. Il conserve tentatives, délais de reprise et échéance
initiale à travers les redémarrages. `complete_attempt` libère seulement la
tentative et fixe le prochain essai ; une tâche ne disparaît qu'après une
nouvelle vue constitutionnelle où l'obligation n'est plus ouverte. La base
SQLite opérationnelle n'est ni le journal K ni une ancre T et ne confère aucun
droit à celui qui possède une lease.

Le résultat inclut le préfixe, la loi effective et les tâches avec une route
`AVAILABLE`, `TRUST_BLOCKED`, `NO_ROUTE` ou `HUMAN_REVIEW`. Une route déclarée
ne prouve pas son fournisseur. `qualification_work` nomme les routes dont la
qualification en direct a échoué, sans supposer quel contrat T est en faute ni
fermer une obligation constitutionnelle. Une tâche et une signature ne sont pas un droit :
`submit(mode=..., task_id=..., route_id=..., basis=..., envelope=...)` recontrôle
la route et le préfixe puis confie l'enveloppe signée au seul chemin d'admission
du déploiement ; `guard(identity=..., signer=...)` utilise exclusivement son port
d'effet installé. L'agent ne reçoit jamais ces credentials.

Cette couche couvre la projection et le passage à K/T, pas le provisionnement
des personnes, clés, ancrages et fournisseurs physiques. L'opérateur doit encore
isoler l'agent du processus de confiance, installer des producteurs de preuves
indépendants, la garde d'effet exclusive, des travailleurs BUILD/RUN et leurs
méthodes, la livraison des escalades et une surface humaine. Le cycle M2 reste une autre
implémentation de démonstration ; aucune équivalence de production n'est établie.
