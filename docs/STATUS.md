# État du projet et source de vérité — 9 octobre 2026

> Document de navigation. Il ne constitue ni une attestation de conformité, ni une preuve d'exécution, ni une autorisation.

## État vérifiable dans main

- **Produit visé** : service géré, AI-first, destiné à construire puis surtout maintenir des dépôts sous une loi explicite.
- **Socle existant** : prototype Python V7 de la TCB, avec admission déterministe, loi composée FLOOR-0 / floors / loi client, journal signé et épinglé, second vérificateur restrictif, réservation et contrôle du passage à l'effet, projection de redevabilité.
- **M2** : outillage de démonstration et de projection de maintenance, non équivalent à un service autonome déployé et validé.
- **Refonte** : `docs/COEUR-STABLE.md` formule les contrats cibles après les 18 constats V7/M2. **Proposé, non implémenté** ; les constats ne sont pas clos par la documentation.
- **Production** : aucune garantie de contrôle exclusif d'un fournisseur réel, de consensus multi-hôte, de certification réglementaire ou de preuve formelle n'est établie par le seul dépôt.

## Architecture : deux périmètres à ne pas confondre

**Noyau logique déterministe** : juge les entrées sur un état et une loi nommés, produit le delta et les décisions d'autorité. Il n'appelle ni IA ni fournisseur pour décider.

**TCB / frontière de confiance** : englobe aussi canonicalisation, cryptographie, signatures, admission/persistance, second vérificateur, horloge de décision, guard, mécanisme d'exécution et adaptateurs capables d'effets. Un noyau petit ne rend pas à lui seul la TCB petite ou sûre.

En dehors de la décision d'autorité : agents, planification, collecteurs, scanners, vues opérateur et dossiers de conformité. Une source dont les affirmations débloquent une action reste une **dépendance de sûreté à qualifier** même lorsque son code est physiquement hors de la TCB locale.

## Contrats cibles de stabilisation

Le cœur devrait gouverner la relation **exigence — sujet — preuve — obligation — autorité — effet**, au moyen de cinq contrats : **transition, temps, preuve, effet, obligation**.

- Une entrée permise n'est pas une transition effectuée correctement : le delta attendu doit être exhaustivement validé.
- Temps signé, temps attesté et temps courant de départ ont des usages différents.
- Une preuve est qualifiée sur son sujet exact, son contrat, sa méthode, sa couverture, sa provenance et sa validité.
- Une autorisation logique n'est pas une garantie d'effet physique : credentials, destination, préconditions, atomicité et reprise sont des frontières réelles.
- Une obligation décrit un manque ; elle ne crée jamais une permission. Le succès d'un effet n'établit pas, sans vérification, la satisfaction de l'exigence.

## Budgets et mesures

`tcb-budget.json` définit trois **plafonds**, pas des métriques d'utilisation actuelle : sûreté **2 942**, restrictif seul **537**, visibilité **500**, soit **3 979** lignes physiques de plafonds cumulés. Les adaptateurs déployés capables d'effets appartiennent au périmètre de confiance, quel que soit leur dossier.

`validation/summary.json` est un **instantané historique V6** (3 244 lignes, 121 tests, statut bloqué). Il ne prouve pas le budget, les tests ni le statut courant de V7/M2. Pour une mesure actuelle, exécuter `make check` sur le commit évalué et archiver les sorties avec le SHA.

## Sources documentaires

- `README.md` : point d'entrée et commandes.
- `docs/VISION.md` : vision produit et séparation des responsabilités.
- `docs/TCB.md` : garanties et limites de la frontière de confiance.
- `docs/COEUR-STABLE.md` : cible architecturale et portes de validation des 18 constats.
- `docs/M2.md` : scénario M2, composants et limites de la démonstration.
- `docs/REVUE-V6.md`, `docs/ANALYSE-V6.md` et `validation/summary.json` : archives de contexte V6, **non** statut de la branche main actuelle.

Aucune mise à jour documentaire ne modifie la release adoptée, la genèse, les journaux, les preuves ni les autorisations.
