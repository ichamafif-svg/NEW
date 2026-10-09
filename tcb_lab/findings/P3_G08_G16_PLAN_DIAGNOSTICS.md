# IV-E — G08/G16 : mécanismes de retrait et décisions d'ordonnancement

**Campagne lancée le 2026-10-09.** Recherche empirique exclusivement. Le noyau historique, la constitution, les opérateurs de maintenance et le scope restent intacts.

## Origine

La [première interprétation IV-D](P3_G08_G16_FIRST_INTERPRETATION.md) a constaté sur un même dépôt dégradé **18 cycles sur 20 sans sujet actif** après deux propositions retirées. Ce résultat ne démontre ni la perte d'une dette G08 ni une violation G16. Le contrôle « sain » de la première exécution était invalide ; la configuration a depuis été corrigée.

## Nouvelles expériences IV-E

Le script [p3_ive_g08_g16_plan.py](../experiments/p3_ive_g08_g16_plan.py) conduit deux scénarios sur huit cycles avec journaux de signatures et dépôt Git local réel : **écart persistant avec échecs répétés** et **contrôle initialement sans vulnérabilité ni advisories synthétiques**.

À chaque cycle : phase de *chaque* proposition, cible logique et ressource complète, signal `proposed/withdrawn` de l'agent, faits signés du scanner, préconditions de décision, actions prévues par `lifecycle.plan`, clés d'obligations visibles, horloge et modification de main. La chronologie permet de départager une attente légitime, un retrait justifié par fait scanner et une absence de nouveau travail malgré un écart persistant.

**Limites :** un plan d'action disponible n'est pas un effet physique effectivement exécuté ; une liste `obligations` vide ne prouve pas l'absence de dette canonique ; l'absence d'action planifiée n'est pas équivalente à l'absence d'escalade dans un autre sous-système. Les expérimentations sont synthétiques, non distribuées.

## Questions à clore sans hypothèse cachée

**G08 — identité et échéance.** Exiger un objet de dette stable `(exigence, sujet canonique, ouverture, échéance)` indépendant de l'identité des propositions. La preuve d'une clôture doit concerner la cible et la méthode exigée. IV-E ne fabrique pas cette preuve : si elle n'est pas observable, G08 reste `OPEN_SEMANTIC`.

**G16 — progrès conditionnel.** Sous hypothèses explicites de disponibilité, équité et chemin d'action permis, observer une réparation vérifiée ou une escalade bornée ; il ne suffit pas qu'une proposition ait existé ni que l'agent cesse de travailler. IV-E explore l'absence de plan ; le canal d'escalade et le budget de délais devront être vérifiés par une attaque séparée avant de fermer G16.

## Statut

**CODED, WIRED_TO_CI, RESULTS_PENDING_VERIFICATION** à la création du document. Relever le run et les cas exacts dans [l'issue d'exécution](https://github.com/ichamafif-svg/NEW/issues/2). Un job vert atteste l'exécution du harnais, pas que Standard a réussi G08/G16.
