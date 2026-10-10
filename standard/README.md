# Surface commune BUILD/RUN

Depuis la racine d'un dépôt équipé, `python -m standard` donne directement
la première tâche autonome accessible, sa loi et ses preuves. `AGENTS.md`
est le point d'entrée lu automatiquement par les agents qui prennent en charge
ce mécanisme. L'installation U peut être déclarée dans `.standard/agent.toml`
ou par `STANDARD_AGENT_CONFIG`; le contrôleur K/T reste un autre processus.
En l'absence d'installation, la commande affiche des indices du dépôt
explicitement non qualifiés, sans prétendre qu'une loi est active.
Pour une autre tâche, `python -m standard context --config CONFIG --task ID`
donne uniquement la loi,
la dette, les preuves et les T pertinents pour cette tâche. Le contexte est
du texte lisible, lié au préfixe et au digest de la loi signée. L'agent n'a
pas à parcourir des README ni une sérialisation de la constitution. Le même
surfaçage ciblé est transmis à l'agent M2. Une erreur de digest refuse la vue.
`python -m standard context --law SECTION/ID` montre la déclaration active
complète, qu'elle vienne des floors ou du client, depuis le même préfixe.
La vue générale les inventorie ensemble. Toute exigence active produit des
besoins de routes et de T, même en l'absence de route installée ou d'écart
déjà attesté ; cette projection est du travail d'installation, pas une preuve
que le fournisseur ou les T existent physiquement. Leur qualification reste
indépendante.

Dans un dépôt maintenu, les règles **propres au client**, hors des floors,
s'écrivent dans `.standard/law.toml` suivant les champs bornés du noyau.
[`examples/client-law.toml`](examples/client-law.toml) montre les identités,
une opération et des exigences supplémentaires. `python -m standard law-source
--source .standard/law.toml` en montre la proposition et vérifie sa composition
avec les floors ; ce fichier ne modifie jamais la loi active. La genèse ou le
changement de loi signé et activé reste nécessaire. TOML n'est ni CSL, ni un
second interpréteur ; il est lu comme les mêmes déclarations typées que K juge.

`StandardService` projette les obligations du noyau sur des tâches stables à partir
d'un `GatewayClient` relié à un `GovernedDeployment` installé dans **un autre
processus** et de routes déclarées par l'opérateur. Une
route décrit le mode, le sujet, le besoin et les contrats T nécessaires. Le
service contrôle leur disponibilité en direct et conserve les trous visibles.

```python
from standard import GatewayClient, Route, StandardService

service = StandardService(GatewayClient("/run/standard/admission.sock"), [
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
du déploiement. La socket n'expose ni guard, ni clés, ni ports fournisseur.
L'agent ne reçoit jamais ces credentials.

La loi effective épinglée porte `ops.<nom>.trusted` : liste de contrats T
supplémentaires exigés pour l'effet. T07 et T08 sont des minima de toute
opération et ne peuvent être retirés par la loi client. La projection du
travail ajoute T06 aux mesures et preuves, T08 à la réconciliation et T07/T08
à BUILD ; une route installée peut seulement demander davantage. Elle est
requalifiée sur ce minimum pour chaque tâche. Lors de l'effet, le port du
guard requalifie le contrat de l'opération sous la loi courante, après le
jugement du noyau et avant le premier octet fournisseur. Une intention
signée peut subsister si un port manque ; la route BUILD et le départ de
l'effet restent bloqués. `submit` refuse une enveloppe qui ne traite pas
exactement la tâche et sa ressource.

Le processus opérateur est assemblé par `hybrid_kernel.install.install` avec
un pin externe de genèse, des pins durables, une évaluation signée et des clés
d'évaluateur épinglées hors agent, une horloge, un port d'effet, un readback
indépendant, le signataire guard et, le cas échéant, la livraison d'escalades.
`TrustedController.serve()` traite les propositions et effectue ses propres
passes de départ/réconciliation/livraison. Le démarrage doit vérifier le
manifeste du code **avant import et avant accès aux secrets** via
`python bootstrap.py CODE_PIN --control adapters.production CONFIG` ; le module
`adapters.production` doit être inclus dans le manifeste de release épinglé et
exposer `serve(config)`. Le fichier CONFIG est propriétaire uniquement.
L'installation ne génère pas de genèse de secours et ne substitue aucun T local
à un T absent. La permission Unix de la socket et les comptes OS distincts sont
des prérequis physiques à vérifier sur l'hôte, non une propriété du protocole.

L'interface U propose `python -m standard discover --repo REPO`, puis
`context`, `status`, `dashboard`, `claim`, `submit`, `attempt`, `run` et `watch` avec `--config`.
Le fichier de configuration U en TOML contient `socket`, `work_db`, `routes` et
éventuellement `workers` (route, commande en tableau, répertoire et timeout).
Voir [`examples/agent.toml`](examples/agent.toml). Les anciennes configurations
JSON restent lisibles pour ne pas casser les installations existantes ; elles
ne sont pas la surface des lois pour les agents.
Un travailleur externe lit la vue constitutionnelle contextualisée en texte
sur stdin. Il renvoie une enveloppe signée par son identité U sur stdout ;
la sérialisation de cette enveloppe reste un protocole interne, pas une loi à
lire ou écrire par l'agent.
`run` lui transmet une tâche louée, puis la renvoie à K/T pour jugement ;
`watch` répète les passages sous un superviseur U. Aucun
retour de travailleur ne ferme la dette ou ne déclenche directement un effet.

Le tableau HTML est une surface de lecture. Les catégories de découverte sont
`PRESENT_UNQUALIFIED` ou `NOT_FOUND` ; les routes qui échouent aux T produisent
du travail de qualification distinct de la dette constitutionnelle. L'opérateur
doit encore fournir et qualifier les personnes, clés, ancrages, fournisseurs,
workers et instruments réels. Le cycle M2 reste une autre implémentation de
démonstration ; aucune équivalence de production n'est établie.
