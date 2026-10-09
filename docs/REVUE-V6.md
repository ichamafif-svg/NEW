# Revue V6 : attaques, réduction, budgets

Trois travaux sur la V6 telle que fournie, sans modifier le code de `tcb/`.

1. Une revue adversariale, menée par un relecteur indépendant. Elle a trouvé **9 violations confirmées** de garanties revendiquées, dont **2 hautes**.
2. Une relecture ligne à ligne de `kernel.py` et de `law.py`. Elle ne dégage qu'**environ 20 lignes** de réduction réelle, ce qui ne règle pas le budget.
3. Un **découpage du budget en trois**, chacun nommé par la garantie qu'il porte. Il est vérifié mécaniquement, et la sûreté tient en 2 246 lignes sur 2 942.

Les scripts de reproduction sont dans `validation/adversarial/`. On les lance depuis la racine avec `python3 validation/adversarial/<script>.py`.

## 1. Revue adversariale

| # | Gravité | Garantie violée | Où | Problème | Repro | Correctif minimal |
|---|---|---|---|---|---|---|
| 1 | **Haute** | Réservation à usage unique (F0-9) | `kernel.py` 638-650, 672-682 | `reconcile:{intent}` s'ouvre dès la réservation, avant l'envoi. Un réconciliateur peut déclarer `not_applied` dans cette fenêtre, ce qui débloque une relance. Le premier gardien envoie quand même, car `judge_dispatch` vérifie seulement « réservé, non exécuté ». Résultat : **deux effets physiques pour une intention**, avec des clés de déduplication différentes. | `r1_reconcile_then_dispatch.py` | Au départ, exiger que `reconcile:{intent}` soit encore ouvert, dans les deux juges. Ou refuser la réconciliation d'un jeton réservé et non exécuté. |
| 2 | **Haute** | Les floors ne s'affaiblissent pas ; veto, révocation et gel sont immédiats | `obligations.py` 351-362 | Une obligation de niveau `refuse` qui a pour `gate` `veto`, `revoke`, `freeze` ou `flag` **désactive ces restrictions**. Une seule loi adoptée suffit. Si la porte porte sur `checkpoint` ou `activate`, le journal se fige. | `r2_law_disables_restrictions.py` | Interdire, à la validation, toute règle bloquante sur les types restrictifs, sur `checkpoint` et sur `activate`. |
| 3 | Moyenne | Un désaccord entre juges arrête, sans contournement | `obligations.py` 409 contre `invariants.py` 439-441 | Avec un booléen sur un chemin pointé (`args.force`), le noyau ignore la porte et le second juge l'applique. **N'importe quel agent peut arrêter le journal**, gels compris. | `r6_nested_bool_where_halt.py` | Même lecture des chemins pointés dans les deux juges, ou refuser les booléens dans `where`. |
| 4 | Moyenne | Un fait n'autorise une action que s'il vient d'une chaîne indépendante (F0-8) | `kernel.py` 527-528, `invariants.py` 331 | Le prédicat `open` lit les obligations ouvertes **sans contrôle d'indépendance**. L'agent ouvre lui-même la fenêtre qui l'autorise. | `r3_open_predicate_self_attested.py` | Étiqueter les instances avec leur provenance et filtrer `opened` par indépendance dans les deux juges. |
| 5 | Moyenne-basse | Restrictions immédiates | `kernel.py` 238-242 | Un auteur horodate une entrée à `anchor_at + MAX_AHEAD`. Jusqu'au checkpoint suivant, **plus aucune entrée n'est admissible, gels compris**. Il peut recommencer à chaque checkpoint. | `r9_time_ceiling_starves_restrictions.py` | Exempter les restrictions de la borne haute, ou leur permettre `at == last_at`. |
| 6 | Basse-moyenne | Une dette ouverte ne voit pas son échéance reculer | `accountability.py` 139-163 | **Renommer une cible remet son échéance à zéro** et supprime l'escalade. | `r4_target_rename_resets_debt.py` | Reporter l'écart ouvert par `(ressource, propriété)`. |
| 7 | Basse-moyenne | La loi client n'affaiblit pas les floors | `law.py` 127-131 | Le client ajoute un type de preuve qui solde `proof` au niveau `unknown`. | `r5_client_weakens_proof_floor.py` | Dans `compose`, exiger que tout solde de `proof` ait un niveau au moins égal à celui du floor. |
| 8 | Basse | Disponibilité | `invariants.py` 147 | Un type de preuve nommé comme une méthode interne (`use`, `quorum`…) déclenche un `TypeError` dans le second juge, donc **un arrêt persistant**. | `r7_evidence_name_collision_halt.py` | Une table explicite des gestionnaires, limitée aux types du noyau. |
| 9 | Basse | Pas de clé répétée dans la racine | `kernel.py` 92-98, `crypto.py` 237 | Une même passkey P-256, encodée en point compressé puis non compressé, est **enrôlée comme deux humains**. | `r8_same_passkey_two_humans.py` | Canonicaliser le point avant de calculer `keyid`. |
| 10 | Basse (plausible) | Reprise après crash | `ledger.py` 213-218 | L'épingle est retenue avant le commit, mais l'entrée candidate n'est pas stockée. Un crash entre les deux peut bloquer le journal pour de bon. | non exécuté | Écrire l'entrée candidate à côté de l'épingle. |

Deux autres constats de faible gravité :
- L'enveloppe DSSE n'est pas une forme fermée : des champs non signés et des signatures dupliquées changent les octets de l'entrée et la tête du journal sans signataire (`r10_envelope_unsigned_fields.py`).
- Un observateur peut pousser le nombre de faits au-delà de 20 000 et rendre `BOUND.EXCEEDED` les effets conditionnels des autres acteurs (plausible).

**Ce qui a tenu :**
- 14 400 entrées signées hostiles, de tous types, n'ont produit que des refus et aucune exception (`fuzz_decide.py`).
- JSON canonique : clés dupliquées, flottants, `-0`, surrogates et octets non canoniques sont refusés.
- Liaison au domaine, quorum compté sur des identités distinctes, veto et dépassement, propositions liées à la racine et à la loi.
- Atténuation, budgets, indépendance des chaînes, inversion des templates.
- Usage unique face à deux gardiens en course et à un redémarrage.
- Épingles, détection de fourche et de régression, audit dépassé refusé.

## 2. Réduction de `kernel.py` (703) et `law.py` (268)

Le code est dense et ne contient pas de duplication notable : les réductions réelles sont faibles.

| Endroit | Réduction | Gain estimé |
|---|---|---|
| `law.py` 144-147 et 154-156 | Contrôle « tighten est une map » fait deux fois | −4 |
| `law.py` 157-176 | Les deux boucles `tighten` (cibles, obligations) passent par une table commune | −6 |
| `law.py` 242-258 | Validation de `ttl`, `delays`, `witnesses` et `controls` par un même assistant | −6 |
| `kernel.py` 329-332 et 358-359 | Réutiliser `_witnesses_available` avec le quorum en paramètre | −2 |
| `kernel.py` 614, 633, 648 | Fusionner « réautoriser puis contrôler le profil » dans `_token`, `_reservation` et `judge_dispatch` | −4 |
| **Total** | | **≈ −20 lignes** |

Les correctifs de la section 1 vont dans l'autre sens : environ +30 à +60 lignes dans le budget de sûreté. **On ne passe pas sous les 2 942 lignes en taillant sans perdre des garanties.** C'est ce qui justifie la section 3.

## 3. Budgets par garantie

Le critère : si ce code ment ou bugue, un acte interdit peut-il passer ?

| Budget | Lignes / plafond | Justification vérifiée |
|---|---|---|
| Sûreté | **2 246 / 2 942** | — |
| Restrictif seul (`invariants`) | 503 / 503 | Il juge seulement après une admission du noyau, et son échec arrête. Un second juge qui accepte tout n'admet rien de ce que le noyau refuse. Un second juge en panne arrête le journal et n'envoie rien (`tests/test_budget_classification.py`). Seuls `ledger`, `guard`, `worker` et `__init__` peuvent l'importer. |
| Visibilité (redevabilité) | 495 / 495 | Aucun module de sûreté ne l'importe (vérifié par `check_tcb.py` et par le test). |

Ces deux derniers plafonds sont des cliquets : ils ne peuvent que baisser. Total : 3 244 lignes, chacune comptée une fois.

**Limite du classement** : un défaut du budget « restrictif seul » ou « visibilité » reste grave pour la disponibilité ou la visibilité, comme le montrent les constats 3, 6 et 8. Le découpage ne les déclasse pas en sûreté secondaire : il nomme la garantie qu'ils portent.

## Recommandation

Corriger d'abord les constats 1 et 2, puis 3 à 5, puis le reste, chacun avec son script transformé en test de non-régression. Le budget de sûreté a la marge nécessaire (environ 700 lignes).

## 4. Corrections par cause racine (appliquées)

Les 10 constats se ramènent à 4 causes. Chaque cause est fermée par une structure, pas par un cas particulier.

| Cause | Constats | Structure ajoutée | Où |
|---|---|---|---|
| 1. Polarité appliquée seulement au portail | 2, 5, 7, saturation | Une obligation bloquante ne peut viser que des types qui agissent, attestent ou atténuent. Un client ajoute des façons de prouver, jamais à un niveau inférieur aux floors. Une restriction peut partager le dernier instant. Une condition ne voit que les faits qu'elle nomme, pour la ressource qu'elle juge. | `obligations.validate`, `law.compose`, `kernel._decide`, `kernel._facts`, et le second juge |
| 2. Cycle d'effet implicite | 1, 10 | Un automate unique `LINE` dans FLOOR-0, lu par les deux juges. Une réservation part dans `DISPATCH_MS` ou jamais, et n'est réconciliable qu'ensuite. L'entrée exacte est conservée avant l'épingle, et `recover_tail()` la restaure sans candidat. | `floor0`, `kernel._line`, `judge_dispatch`, `invariants._line`, `pins.keep`, `ledger.recover_tail` |
| 3. Identité sur la représentation | 6, 9, enveloppe | Une clé n'a qu'un encodage canonique. Une enveloppe est une forme fermée, une signature par clé, triées. Une dette suit le couple `(ressource, propriété)` qu'elle mesure, pas le nom de sa cible. | `crypto.canonical_public`, `crypto.open_envelope`, `sign`, `accountability._sync` |
| 4. Provenance et jointure par listes | 3, 4, 8, et les portes | Les instances d'obligation portent l'étiquette de provenance de leur ouvreur. Une fenêtre (`open`) ou une porte ouverte par la chaîne de l'acteur ne lui sert pas. `where` n'accepte que des chaînes et des entiers. Le second juge appelle ses gestionnaires par une table explicite. Un test différentiel aléatoire de 400 pas vérifie que les deux juges ne divergent jamais. | `kernel._law_obligations`, `obligations.step(admits)`, `invariants` (`HANDLERS`, `_law`, `_authority`), `tests/test_root_causes.py` |

**Constat ajouté pendant la correction.** Une porte d'obligation (`gate`) avait le même défaut que le prédicat `open` : un acteur pouvait ouvrir lui-même la porte qu'il devait franchir. C'est fermé de la même façon. Effet de bord accepté : avec `reopen: keep`, le premier ouvreur garde l'instance. Un acteur qui l'ouvre lui-même ne se bloque que lui-même ; `reopen: replace` laisse une source indépendante la remplacer.

**Vérification.**
- Les 10 scripts d'attaque échouent désormais.
- `tests/test_root_causes.py` : 13 tests, dont le test différentiel.
- Suite complète : **136 tests réussis**. Le seul échec restant teste le confinement seccomp, inapplicable dans le conteneur de vérification ; il échoue aussi sur l'archive d'origine.
- Les tests de santé ont été exécutés sur une copie jetable où seul le verrouillage seccomp était neutralisé. L'archive d'origine, dans les mêmes conditions, donne 120 tests réussis.
- Un test existant a été adapté (`test_double_reservation_is_refused_by_the_store_when_both_checks_fail`). Le nouvel automate arrête désormais la double réservation avant la contrainte SQL ; le test désactive aussi l'automate, pour continuer à vérifier la dernière ligne de défense.

**Budgets.**

| Budget | Lignes / plafond |
|---|---|
| Sûreté | 2 355 / 2 942 |
| Restrictif seul | 537 / 537 |
| Visibilité | 500 / 500 |

Les deux plafonds de cliquet ont été relevés par décision consignée dans `tcb-budget.json` (+34 et +5), plutôt que par compaction du code. Le format change : FLOOR-0, l'état (`line`), la table `tail` des épingles et la forme des enveloppes. Il faut une genèse neuve.
