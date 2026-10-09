# Phase 3 — protocole d'exploration continue (NON DESIGN)

**Objet :** expliquer ce que la TCB fait, ce qu'elle doit faire et dans quelles conditions, pour que Standard puisse maintenir un dépôt en autonomie sous gouvernance. **Le scope reste figé.** Il est interdit d'utiliser les observations P3 pour choisir, implémenter ou orienter prématurément un CIR, une algèbre, un DSL ou un refactoring.

## Boucle obligatoire

1. **Observation vérifiée** — commit, run, état, entrée, verdict, effets et hypothèses.
2. **Questions ouvertes** — jusqu'où cette observation tient-elle ? Quelles hypothèses sont cachées ?
3. **Hypothèses alternatives** — bug d'oracle, bug de fixture, restriction délibérée, faille de décision, faille de frontière physique ou problème de progrès.
4. **Contre-expériences** — changer une seule dimension, puis combiner plusieurs : signataire, temps, loi, ordre, préfixe, panne, oracle, journal, fournisseur.
5. **Résultat qualifié** — CONFIRMED, REFUTED_UNDER_ASSUMPTIONS, INCONCLUSIVE, NOT_RUN, BLOCKED ; conservation des traces.
6. **Nouvelle profondeur** — écrire les questions que le dernier essai ne résout pas.

**Aucun résultat ne déclenche un changement d'abstraction ou de scope.** Les phases 4–8 restent hors mandat de ces campagnes.

## Priorités empiriques immédiates

- **Échecs rouges historiques :** expliquer `test_rule6_red_tests_withdraw_and_free_the_target` ; distinguer bug de règle autonome, test fragile, mauvaise simulation et effet TCB.
- **Preuves et obligations :** tenter d'établir ce qui reste ouvert quand une exécution réussit mais que le contrôle cible reste dégradé.
- **Séquences longues :** varier les ordres des opérations valides/interdites, regarder la continuité des obligations et la récupération de capacité légitime.
- **Pannes et temps :** crash pin/journal, incertitude après départ, fenêtre de dispatch, réconciliation.
- **Indépendance physique :** documenter concrètement les hypothèses liées aux clés, hôtes et fournisseurs ; les tests locaux ne les prouvent pas.
- **Autonomie :** exiger dans chaque famille un oracle de progression légitime, ou la justification d'un arrêt conservateur.

## Discipline

Une expérience qui passe n'est pas « preuve du scope ». Un test rouge n'est pas automatiquement une faille constitutionnelle. Un test qui écrit lui-même son verdict attendu ne vaut pas oracle indépendant. En priorité approfondir les comportements contradictoires et ambigus plutôt que multiplier les cas quasi identiques.
