# IV-H — G08 obligation cible et G16 condition d'escalade

**2026-10-09 — expérience soumise à GitHub Actions, résultats non encore confirmés.** Le noyau, les règles et le scope restent inchangés.

## Résultat IV-G retenu
Sur sept cycles, dont une variante couvrant environ cinquante heures simulées, le `journal.health` conserve 21 éléments ouverts et 0 escalade. Les objets de type `target` présentent notamment `obligation`, `subject`, `opened` et `due`. Ces observations **ne démontrent pas** la stabilité de la dette spécifique `target:vulns` ; le total constant pourrait masquer des substitutions.

## Expérience IV-H
Le script [p3_ivh_canonical_vulns.py](../experiments/p3_ivh_canonical_vulns.py) suit spécifiquement `target:vulns` et compare les champs `obligation/subject/opened/due/owner/needs` au cours de huit cycles, avec deux sauts temporels de 25 h, en parallèle des retraits, des nouvelles propositions et des entrées `proven/escalated`. Il relève également la spécification de la cible via `ops.cycle.TARGETS`.

**Oracle G08 local :** `persistent_same_open_identity` indique si exactement le même objet ouvert demeure présent tout au long du scénario. Une valeur vraie serait un constat de continuité **dans cette fixture seulement**, pas une garantie de persistance sous rollback, renommage, changement de loi ni fermeture par preuve externe.

**Oracle G16 :** vérifier la présence d'une escalade dans la fenêtre, puis la comparer à la date `due` et à une éventuelle règle d'escalade normative. **Zéro escalade avant échéance** n'est pas automatiquement un défaut. L'expérience n'invente pas de deadline d'escalade.

## Décision de recherche
G08 et G16 restent `OPEN_SEMANTIC` jusqu'à lecture de la sortie IV-H et examen de la propriété demandée. Les autres frontières conservent leur classification conditionnelle, sans preuve physique supplémentaire. Les runs officiels sont dans [le registre du laboratoire](https://github.com/ichamafif-svg/NEW/issues/2).

## Statut de clôture fonctionnelle (2026-10-09)

Voir [FUNCTIONAL_BOUNDARY_FREEZE_DECISION.md](../FUNCTIONAL_BOUNDARY_FREEZE_DECISION.md) : **16/16 allocations K/T/U figées conditionnellement**, sans certification des garanties ni du déploiement. Les constatations et limites ci-dessus restent valables comme faits historiques/conditions d'audit ; elles ne constituent plus un blocage de **délimitation du noyau**. La validation physique, les preuves empiriques et les portes de sortie de P3 restent ouvertes ; G08/G16 ne doivent pas provoquer une nouvelle boucle d'audit général du produit.
