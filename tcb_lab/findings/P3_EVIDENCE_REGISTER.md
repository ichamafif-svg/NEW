# Phase 3 — Registre de provenance empirique

**Règle :** une observation n'existe que sous un environnement, un commit, un run/log, un oracle et des limites explicités. Éviter toute extrapolation du vert à des domaines non testés.

| Réf | Source observable | Fait exploitable | Ce que cela NE prouve PAS | Statut |
|---|---|---|---|---|
| EV01 | [Actions #19](https://github.com/ichamafif-svg/NEW/actions/runs/37948321004), log adversarial | traceback d'un script masquée par le pipeline `tee` ; verdict GitHub succès | faille TCB | OBSERVED, instrumentation |
| EV02 | [Actions #25](https://github.com/ichamafif-svg/NEW/actions/runs/37948637779), log et artifact | `P3-02`/`P3-07` inconclusive ; job rouge avec propagation d'erreur | bug de logique canonique | OBSERVED, harnais |
| EV03 | [Actions #30](https://github.com/ichamafif-svg/NEW/actions/runs/37948915737), registre | 59 exercices P3 + 4 G1 lisibles, pas d'ID signalé | robustesse multi-host | OBSERVED_LOCAL |
| EV04 | [Actions #37](https://github.com/ichamafif-svg/NEW/actions/runs/37949668631), registre | 64 exercices P3 + 4 G1 lisibles, zéro ID signalé | liveness globale | OBSERVED_LOCAL |
| EV05 | [Actions #45](https://github.com/ichamafif-svg/NEW/actions/runs/37951191335), [registre #2](https://github.com/ichamafif-svg/NEW/issues/2) | 69 exercices P3 + 4 G1 lisibles et job test success ; long horizon 5 × 80 tentatives | 400 garanties indépendantes ou effets réels | OBSERVED_LOCAL |
| EV06 | [Boundary #60](https://github.com/ichamafif-svg/NEW/actions/runs/37946687408) et plusieurs autres runs rouges | échec récurrent `test_rule6_red_tests_withdraw_and_free_the_target` dans `make check` | faille du noyau démontrée | OBSERVED_FAILURE, CAUSE_OPEN |
| EV07 | [registre #2](https://github.com/ichamafif-svg/NEW/issues/2) | alternance de runs verts et rouges `TCB boundary checks` suivant commits | instabilité du noyau sur *même build* | OBSERVED_HISTORY |

## Limites méthodologiques du registre

L'issue #2 est **vivante** : les statuts `in_progress` changent ; elle ne conserve pas les détails complets de chaque oracle. Les exécutions citées constituent les points d'ancrage historiques. Certaines inférences ci-dessus proviennent du résumé automatique ; pour affirmer une défaillance d'un invariant précis, il faudra consulter le JSON et/ou le log du test spécifique et enregistrer la fixture, le seed et le préfixe.

`CONFIRMED` pour un défaut d'instrumentation n'est pas `CONFIRMED` pour une faille constitutionnelle. Les tests historiques rouges peuvent changer d'issue au gré du commit, sans que l'on ait isolé la cause de la différence.
