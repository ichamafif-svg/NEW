# Phase 3 — Backlog dérivé des findings : profondeur × couverture

**Usage :** choisir les **prochaines expériences**, pas le prochain design. On ne clôt pas une feuille tant que l'oracle n'est pas fiable et que les alternatives explicatives ne sont pas départagées.

| Ordre | Feuille | Pourquoi ces findings la rendent prioritaire | Profondeur cible | Expérience et témoins | Statut |
|---|---|---|---|---|---|
| 1 | O1/R1 — réparation retirée | plusieurs boundary runs rouges ; cause ouverte | D1→D3 | rejouer test rouge, changer un champ, suivre same-subject obligation, observer nouvelle proposition ; témoin permission valide | NOT_RUN approfondissement |
| 2 | E1 — effet inconnu | harnais local uniquement ; risque double action | D2→D5 | ACK perdu + reprise + retry, puis réponse fournisseur tardive ; contrôle no-send et unique-send | NOT_RUN |
| 3 | P1/O1 — preuve trompeuse | signatures ne prouvent pas vérité/coverage | D1→D3 | preuve fausse signée, mauvais SHA, oracle distinct ; obligation avant/après | NOT_RUN |
| 4 | O1 — échéance continue | stress-test sur ressources *distinctes* ; dette d'un sujet non étudiée | D3 | 20/100 tentatives sur même ressource avec CI verte/rouge ; conserver opened/due | NOT_RUN |
| 5 | L/E — loi change pendant départ | autorisation locale isolée | D2→D4 | proposer/activer loi entre token, réserve et re-jugement ; permuter l'ordre | NOT_RUN |
| 6 | T/B — reprise pin+journal | SQLite local, pas de crash injection complète | D4→D6 | kill avant/après point durable, pin ahead/journal behind, restauration indépendante | NOT_RUN |
| 7 | A/P — labels & oracles | indépendance logique peut partager contrôle physique | D2→D6 | clés distinctes, même administrateur/scanner ; vérifier propriété réellement démontrée | NOT_RUN |
| 8 | E/B — concurrence multi-hôte | verrou SQLite local ne vaut pas fence fournisseur global | D4→D6 | deux guards, deux domaines de panne, réconciliation indépendante, vérifier egress | BLOCKED sans environnement dédié |
| 9 | R — BUILD/RUN progressif | objectif de Standard = autonomie gouvernée, pas refus universel | D3→D5 | repo sans/mixte/mature SRE, erreurs répétées, scanner indisponible, contrôle positif d'escalade | NOT_RUN |

## Pour chaque feuille, collecter

`parent_id`, `case_id`, `run`, `commit`, `threat_actor`, `preconditions`, `sequence`, `safety_oracle`, `progress_oracle`, `state_before_after`, `effect_count`, `obligation_identity`, `time_assumption`, `result`, `alternative_hypotheses`, `child_questions`.

## Ordonnancement

On commence par **O1/R1** parce que nous avons un signal rouge réel et des hypothèses contradictoires. En parallèle, E1 et P1 ouvrent les frontières les plus critiques mais encore peu couvertes. Les cas multi-hôtes restent bloqués jusqu'à un environnement et des modèles d'adversaires adéquats. Les tests passent d'abord d'une dimension isolée à deux ordres opposés, puis à un même sujet sur la durée.

Le travail reste **Phase 3 uniquement** ; aucun changement du scope, du noyau, des abstractions ou des contrats produit.

## Interprétation Midpoint II — ordre d'attaque ajusté (sans clôture)

Après analyse des 31 expériences ([P3_MIDPOINT_II.md](P3_MIDPOINT_II.md)) : **O1** dix divergences de l'assertion historique après deux cycles, capturer identité et justification des deux sujets ; **E1** refus `HIST.TIME` masque la cause de redémission, refaire avec temps strictement monotone ; **P1** changer réellement les assertions signées (méthode / coverage / provenance), et non seulement le drapeau de vérité local hors message. Priorités 1–3 **toujours ouvertes**.

## Campagne III : dédoublement des feuilles et statut

- `O1.H1–H4` : 18 séquences codées (`p3_iii_autonomy_subjects.py`), capturent sujets et temps exacts, mais **ne démontrent pas encore** la persistance d'une obligation sur 100 réparations.
- `E1.H1–H4` : 8 séquences codées (`p3_iii_effect_clock.py`), éliminent l'erreur simple de `t+3` en utilisant le dernier horodatage durable, mais pas de crash ni multi-hôte.
- `P1.H1–H4` : 6 contrastes codés (`p3_iii_proof_epistemic.py`) explicitent la séparation entre label de vérité extérieur et contenu signé ; restent ouverts les tests de couverture et méthode attestées par sources distinctes.

Les 6 branches A/L/T/B et croisements demeurent ouverts ; **ne pas promouvoir D4–D7** sur la seule base d'un nouveau rapport vert. Sources : [arbre](../EXPERIMENT_TREE_DEPTH_COVERAGE.md) et [campagne III](P3_CAMPAIGN_III.md).
