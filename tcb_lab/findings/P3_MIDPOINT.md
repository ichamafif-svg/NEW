# Phase 3 — Midpoint empirique : que savons-nous ?

**Snapshot 2026-10-09.** Référence historique `main@d6347dc` ; branche de laboratoire séparée. Ne pas utiliser les résultats pour redéfinir le scope ou choisir une abstraction.

## Observations positives dont les hypothèses sont connues

Le [registre Actions #2](https://github.com/ichamafif-svg/NEW/issues/2) a annoncé, au run `37951191335` (commit `93abec0250`), `adversarial: success`, avec **8 suites P3 lisibles** : 8 signed, 4 effects, 30 mutations, 10 autonomy, 7 compositions, 5 counterexperiments et 5 long horizon = **69 exercices P3**, plus 4 G1, sans identifiant signalé. Cette source est un rapport CI : elle **ne prouve pas à elle seule** l'absence de défaut dans les oracles ou la correction de chaque garantie.

- Des demandes malformées, des pouvoirs absents et des signatures altérées ont été refusés dans les cas ciblés.
- Certaines restrictions entre émission et départ ont bloqué des effets simulés.
- Un résultat fournisseur « ok » ne ferme pas automatiquement sa dette de preuve.
- Cinq séquences seedées de 80 tentatives, réparties sur des ressources distinctes, ont permis des intentions autorisées après des refus. Cela **ne** teste pas l'obligation persistante sur un sujet unique, ni l'effet réel.
- Les effets testés utilisent de faux ports locaux et une discipline SQLite ; aucune conclusion inter-hôtes.

## Observations négatives ou ambiguës

- **Instrumentations de tests :** un ancien pipeline affichait du vert malgré une traceback Python dans un pipeline avec `tee`. Ce défaut a été observé et corrigé au niveau CI ; il s'agit d'un défaut de mesure, non d'une faille constitutionnelle.
- **Oracles de fixture :** comparaison incorrecte d'un snapshot `ReadOnly` avec un objet dict, ainsi que tentative de canoniser des structures internes non JSON, ont produit des expériences `INCONCLUSIVE`. Corrections instrumentales réalisées sans changement de TCB.
- **Boundary checks historiques :** plusieurs runs rouges reproduisent `test_rule6_red_tests_withdraw_and_free_the_target`. Les logs montrent une tentative retirée et une nouvelle proposition, suivies d'une assertion échouée. Une violation du kernel n'est **pas établie** ; un défaut d'attente, de fixture, de logique de maintenance ou de contexte reste possible. Certaines autres exécutions de ce workflow sont vertes selon le commit.

## Hypothèses que les observations ne tranchent pas

1. L'autorité logique correspond-elle aux personnes physiques et aux domaines de possession de clés ?
2. Le re-jugement protège-t-il **tous** les chemins physiques, y compris sous concurrence multi-hôte et credentials alternatifs ?
3. Le statut d'une obligation reste-t-il stable à travers retraits et réparations, quand la CI fluctue ou la cible est renommée ?
4. Une preuve signée, partielle ou mensongère peut-elle débloquer un effet ou fermer une dette ?
5. Un effet « inconnu » peut-il être rejoué lorsque la réponse du fournisseur arrive tardivement ?
6. Après crash/restauration du journal et des pins, les permissions et les effets retrouvent-ils une histoire unique ?
7. Une procédure d'escalade explicite assure-t-elle l'**autonomie conditionnelle** sans affaiblir les restrictions ?

## Trois directions d'expériences — sans prescriptions d'architecture

**A. Le test rouge comme germe d'arbre (O1/R1).** Reproduction minimale, témoins contradictoires, même sujet, deux agents, évènements dans les deux ordres, dette avant/après et effet sur la capacité de continuer.

**B. L'inconnu à la frontière d'effet (E1/B1).** Interleavings délibérés à la réservation, au départ, à l'ACK et à la réconciliation ; crash injection, puis multi-processus et multi-hôtes lorsque l'environnement existe.

**C. La preuve comme permission (P1/O1).** Oracle faux mais signé, preuve périmée, mauvais univers, bonne preuve indépendante, échéance de dette et clôture effective.

Ce midpoint n'est pas une porte de sortie de phase 3. Il décrit seulement **où monter en profondeur et où élargir la couverture**.
