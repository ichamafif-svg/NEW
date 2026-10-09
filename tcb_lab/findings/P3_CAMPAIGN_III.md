# Phase 3 — Campagne adversariale III : registre d'exécution et décisions de recherche

**Statut initial : scripts soumis et CI automatique déclenchée.** Les verdicts individuels seront confirmés via [issue #2](https://github.com/ichamafif-svg/NEW/issues/2), pas inférés du commit. Le [nouvel arbre expérimental](../EXPERIMENT_TREE_DEPTH_COVERAGE.md) est la source de la profondeur et couverture. Aucun changement de scope, kernel ou abstraction.

| Branche | Question discriminante | Suite / cas | Observations attendues dans le rapport | Frontière NON démontrée |
|---|---|---|---|---|
| **E** | `HIST.TIME` masquait-il un vrai blocage anti-double effet ? | `p3_iii_effect_clock.py` — 8 cas | seconde tentative strictement postérieure à `last_at`, verdict exact, appels port, dette, deux handles de journal | double machine, fournisseur réel, crash |
| **O/R** | Quelle cible reste live et à quel moment après retrait ? | `p3_iii_autonomy_subjects.py` — 18 cas | IDs exacts, temps, phases, `main`, groupes `found:1`/`none` à 2/3/5 cycles | continuité d'obligation démontrée, CI externe |
| **P** | Quels contrastes portent sur un contenu signé, et lesquels sont invisibles au kernel ? | `p3_iii_proof_epistemic.py` — 6 cas | sujet, auteur, grade, timestamp, décision et fermeture, doublet vrai/faux externe | source réellement indépendante, vérité physique |

**IMPORTANT :** un rapport `OBSERVED` est une donnée, pas un test de sûreté réussi. Les cas O/R peuvent diverger de l'oracle historique sans échouer la CI. Les cas E qui refusent au prochain temps ne suffisent pas à prouver un verrou distribué. Le doublet P vrai/faux ne change pas le message de preuve lui-même.

## Suite conditionnelle

Si E donne un refus autre que `HIST.TIME`, isoler la cause, puis ajouter la reprise de crash et les contrôles d'egress ; si `HIST.TIME` persiste malgré le temps monotone, inspecter l'horloge attestée/les contraintes de time floor, sans modifier le noyau. Si O produit plusieurs phases à même SHA, retrouver la raison d'obligation et le next-step observé avant de classer correct/incorrect. Si P reproduit l'équivalence vraie/fausse, attaquer ensuite méthode, couverture et vérité testables par oracle réellement distinct ; ne pas confondre ce résultat avec un défaut cryptographique.

## Couverture résiduelle

Les autres branches A/L/T/B, la concurrence déterministe D4, la panne D5, le multi-hôte/fournisseur D6 et la contradiction extérieure D7 **ne sont pas fermées**. La campagne III est une campagne **ciblée** à partir des findings, pas une couverture complète de toutes les garanties.

## Premier diagnostic de CI (sous réserve du run corrigé)

Le premier job III ([Actions #92](https://github.com/ichamafif-svg/NEW/actions/runs/37955599612)) a correctement été **rouge** : le script O/R avait laissé fuiter les messages du simulateur sur stdout et son artefact JSON était illisible. Cette erreur est un **défaut de harnais**, pas un défaut TCB ; le script a été corrigé au commit `23976479b1` en capturant toute la sortie de `Sim`. La vérification du run correctif reste requise.

Les **huit observations E1** du même run sont lisibles : seconde redemption au temps `last_at + 1` ; le cas ACK perdu est cette fois refusé par `OBL.NOT_OPEN`, avec un seul appel au port synthétique, plutôt que par `HIST.TIME`. Cette mesure permet de lever une ambiguïté d'oracle **localement** sans conclure à un fencing global. Les six preuves épistémiques sont également lisibles, mais l'indicateur de vérité reste hors message signé. L'interprétation des 18 séquences O/R attend un artefact JSON valide.

## Vérification post-correction — 9 octobre 2026

Le [run Actions `37956022363`](https://github.com/ichamafif-svg/NEW/actions/runs/37956022363) est **success** avec artefacts III **PARSED** : E=8 observations, O/R=18 observations, P=6 observations, zéro cas III classé inconclusif dans le registre. L'erreur JSON du premier run est donc résolue pour ce run ; elle reste conservée comme constat d'instrumentation. **Ne pas confondre ce succès CI avec une validation de safety/liveness :** les expériences O/R sont descriptives, le fournisseur E est simulé, et le label de vérité P ne figure pas dans la déclaration signée. Les runs historiques continuent de présenter des divergences aux assertions de cycle ; les trois sous-arbres demeurent **ouverts**.
