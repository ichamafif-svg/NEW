# IV-D — G08 + G16 : obligations et progression, expérience longitudinale

**Date : 2026-10-09.** Périmètre constitutionnel inchangé ; aucune modification du kernel/ops. **Statut initial : CODED / CI pending**, sous réserve d'un artefact JSON valide confirmé dans [le registre automatique](https://github.com/ichamafif-svg/NEW/issues/2).

## Questions et oracles contradictoires

**G08 :** dans un écart persistant, la création de nouvelles tentatives ne doit pas réinitialiser silencieusement l'identité de l'exigence, l'ouverture et l'échéance de sa dette. Contre-témoin : une preuve réellement qualifiée et couvrante peut justifier la fermeture ; **un signal scanner `none` ne suffit pas à constituer une telle preuve**. L'oracle opérationnel local suit pour chaque cycle les clés de dette visibles, l'ensemble des sujets de réparation, les sujets nouveaux, la cible, le verdict scanner, la tête main et le temps. **Limite : les sujets `ops` ne sont pas nécessairement les sujets constitutionnels de dette ; cette expérience ne démontre donc pas à elle seule G08.**

**G16 :** sous ressources disponibles, écart persistant et actions permises, observer progression ou escalade ; comparer aux contrôles où la cible devient saine et où elle l'est d'emblée. Mesure : cycles sans sujet actif malgré signal persistant, créations répétées, stabilité de main. Un compte de sujets `live` **ne démontre pas la réparation effective** et l'absence de progression ne prouve pas à elle seule une violation sans contrat de fairness/échéance.

## Quatre cas adversariaux

| ID | Témoin | Temps | Hypothèse testée |
|---|---|---|---|
| G08-red-20 | `found:1` permanent | 20 cycles sur même repo | répétition, retrait, continuité des sujets et des dettes exposées |
| G08-healed-20 | `found:1` puis `none` après 5 cycles | 20 | un signal de guérison n'est pas automatiquement une preuve de fermeture |
| G16-red-20 | `found:1` permanent | 20 | maintenance utile ou escalade vs churn et blocage |
| G16-healthy-20 | `none` | 20 | contrôle sans erreur persistante ; éviter l'activité injustifiée |

Le programme [p3_ivd_g08_g16.py](../experiments/p3_ivd_g08_g16.py) exécute un vrai dépôt Git local sous Sim, signatures/Journal réels du corpus, fournisseurs non physiques. Les retours sont `OBSERVED` (trace), `INCONCLUSIVE` (erreur d'expérience). Les résultats **ne sont pas classés PASS**.

## Conditions nécessaires pour fermer G08 / G16

**G08** exige des traces portant *la même exigence et le même sujet canonique* au-delà des identifiants de proposition, l'instant exact `opened` et `due`, ainsi qu'une vraie attestation de fermeture.

**G16** exige un oracle explicite : si les entrées requises restent disponibles et un chemin autorisé existe, alors **progrès observable ou escalade dans un délai borné**, même avec échec répété, sans laisser l'agent élargir ses droits. Le délai et la fairness restent à étudier, non choisis par ces tests.

Les deux branches restent `OPEN_SEMANTIC` jusqu'à ce que leurs obligations d'observation soient satisfaites et soumises à revue contradictoire.

## G08/G16 — lecture des résultats réels (après Actions 37964069387)

Voir [l'interprétation complète](P3_G08_G16_FIRST_INTERPRETATION.md). Dans les scénarios à écart persistant, deux propositions sont retirées puis **18 cycles / 20 sans sujet live** sont observés, sans modification de main. Les obligations constitutionnelles ne peuvent pas être déduites de la seule liste `state["obligations"]` vide : **G08 reste ouvert**. **G16 reste ouvert** en attente du contrôle des escalades et de la fairness. Le prétendu contrôle sain était **invalide** (le runner `none` n'enlevait pas `vulns=found:2`) et a été rectifié dans le harnais ; ne pas citer l'ancien résultat comme témoin sain. Aucune modification du noyau ou du scope.
