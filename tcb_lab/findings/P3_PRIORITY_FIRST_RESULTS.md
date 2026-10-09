# P3 — Première récolte observée sur les trois priorités

**Run analysé :** [GitHub Actions P3 #59 — 37952372660](https://github.com/ichamafif-svg/NEW/actions/runs/37952372660), job adversarial `113894157094`, logs complets consultés. Environnement : CI Ubuntu local, fixtures signées, port fournisseur simulé. **Ces mesures n'autorisent ni refonte de scope ni conclusion de conception.**

## P0-1 O1/R1 — test historique rouge

`p3_priority_o1.py` a exécuté quatre variantes (dégradation `found:1` à 1, 2 et 3 cycles ; contrôle `none` à 2 cycles). **Dans la variante historique à deux cycles, les trois assertions du test d'origine sont TRUE :** une cible withdrawn, branche main inchangée, aucun sujet encore live. Premier cycle : un sujet `measuring` actif ; deuxième cycle : le sujet original est `withdrawn`, non live.

**Ce que cela change :** les anciens runs rouges n'impliquent pas une panne reproductible à chaque réexécution. Une cause possible reste la variation du dépôt/de la fixture/du timing ou des observations d'un cycle. **À ne pas déclarer réparé** : il faut comparer les versions exactes rouge et verte, les variables non épinglées et les logs du même test avant d'inférer une faute.

**Enfant expérimental :** reproduire plusieurs fois à commit identique et capturer les sujets avant et après cycle, l'ordre et la dernière nouvelle proposition. Ajouter l'assertion `withdrawn` exacte et le test de progression réelle sur sujet toujours dégradé.

## P0-2 E1 — effet à statut incertain

`p3_priority_e1.py` a observé :
- ACK perdu après invocation du port : **1 send**, `executed=unknown`, obligation `reconcile` ouverte, retry `OBL.BLOCKED`.
- Retour `unknown` explicite : même type d'attente de réconciliation, aucun retry automatique démontré.
- Retour `ok` : **1 send**, `executed=ok`, dette `proof` ouverte, nouvel intent `retry_of` admis localement.
- Retour `failed` : **1 send**, `executed=failed`, pas de dette de réconciliation dans cette fixture, `retry_of` admis.

**Question nouvellement ouverte :** un `failed` après invocation du port signifie-t-il physiquement « non appliqué » pour **tous** les adaptateurs ? Le harnais a compté un appel dans les quatre cas. Il ne peut pas démontrer si un fournisseur a agi. Étudier précisément les conventions `NotDispatched` / `failed` et les réponses partielles. Autre question : `retry_of` après `ok` peut être légitime, mais mérite contrôle selon non-idempotence et preuve de cible.

## P0-3 P1/O1 — attestation fausse, signée correctement

`p3_priority_p1.py` a observé :
- Sujet exact et drapeau externe `true` : attestation `readback` admise ; dette `proof` fermée.
- **Même sujet et drapeau externe `false` : attestation également admise ; dette `proof` fermée.**
- Sujet différent mais signature valide : refus `PROV.SUBJECT` ; dette `proof` conservée.

**Interprétation limitée mais importante :** la TCB historique vérifie ici l'attribution et l'identité du sujet, mais ne peut pas vérifier la vérité physique derrière la déclaration signée. C'est une **frontière de confiance démontrée par la fixture**, pas une faille de cryptographie ni une preuve que toute fausse observation donne une permission. Les prochaines attaques devront distinguer procédure de qualification, méthode, couverture, compromission de l'oracle et vérité externe.

## Questions et couverture non fermées

**O1 :** pourquoi certains runs historiques rouges et ce témoin vert ? Quel paramètre explique la divergence ? Observations d'obligations et coexistence de sujets non encore effectuées.

**E1 :** que devient la séquence lors d'un ACK tardif, d'une application partielle, d'une restauration, ou de deux writers/hôtes distincts ?

**P1 :** quel instrument peut certifier la vérité, la couverture et la bonne méthode ? Que se passe-t-il quand deux identités partagent la même source ?

Ces trois priorités restent **ouvertes**. La profondeur atteinte est essentiellement locale D1/D2 ; D3–D7 ne sont pas acquis. Elles gouvernent les enfants suivants du [backlog](P3_DEPTH_COVERAGE_BACKLOG.md) et de l'[arbre](../EXPERIMENT_TREE_DEPTH_COVERAGE.md).

La CI et les résultats restent accessibles automatiquement via [issue #2](https://github.com/ichamafif-svg/NEW/issues/2).
