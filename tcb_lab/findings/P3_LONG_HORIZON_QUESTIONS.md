# P3 — Questions issues des premiers essais de durée (à explorer, pas à résoudre)

**Statut : investigation en cours.** Ce document ne propose ni modification de scope, ni nouvelle architecture, ni changement d'abstraction. Les simulations ci-dessous utilisent le journal local signé, jamais un fournisseur réel.

## Expériences instrumentées dans cette itération

`experiments/p3_long_horizon.py` utilise cinq seeds reproductibles `1, 7, 29, 113, 991` × 80 entrées, soit **400 tentatives**, en combinant intentions légitimes, capacités inexistantes et arguments malformés. Chaque tentative vérifie le verdict, l'absence de mutation en simple admission, et la continuation possible après refus. Les sous-scénarios ne sont pas indépendants et **ne représentent pas 400 garanties vérifiées**.

Questions auxquelles cette expérience répond localement si elle passe :
- Un refus d'entrée influence-t-il la transition légitime suivante ?
- La sérialisation signée conserve-t-elle des sujets distincts à travers des dizaines de tentatives ?
- L'oracle de progression peut-il confirmer un changement d'état authentifié sans envoyer aucun effet ?

Questions auxquelles elle **ne** répond **pas** :
- Comment évoluent les obligations lorsqu'un effet réel reste inconnu ?
- Le départ reste-t-il exclusif en multi-hôte, sous partitions et crash ?
- Le scanner qualifie-t-il la bonne cible et le bon commit ?
- Une loi ou racine modifiée pendant une longue tentative invalide-t-elle les permissions précédentes ?
- Les agents se bloquent-ils mutuellement en maintenant la même ressource ?
- Quelle garantie de progression persiste lorsque témoins, journal ou fournisseur cessent d'être disponibles ?

## Nouveau plan d'expériences dérivé

| Ref | Question falsifiable | Dimensions à permuter | Contrôle positif | Contrôle négatif | Priorité |
|---|---|---|---|---|---|
| QP3-01 | Un effet `unknown` empêche-t-il toute répétition jusqu'à réconciliation indépendante ? | retry, délai, readback, autre actor | reconcilier puis réessayer | retry avant readback | P0 |
| QP3-02 | La dette de preuve reste-t-elle liée au sujet d'origine malgré une succession de repairs ? | 20 repairs, nouveau commit, timeout | preuve exacte du sujet | preuve d'un autre commit | P0 |
| QP3-03 | Peut-on avoir deux départs pour une cible sous deux guards/hôtes ? | stockage, crash, partition, provider delay | départ unique authentifié | 2 départs | P0 |
| QP3-04 | L'interdiction de nouvelle autorité tient-elle lorsque la loi change entre planification et départ ? | avant/après token/reservation | nouvelle intent sous loi active | ancienne intent réutilisée | P0 |
| QP3-05 | Les signatures et labels prouvent-ils suffisamment l'indépendance de la preuve ? | doubles clés, identité physique, source commune | oracle indépendant vérifiable | auto-validation | P0 |
| QP3-06 | Que signifie progresser sans agent souverain dans une longue suite d'erreurs et de blocages ? | refus, scanner down, time gap, budget | réparations encore légitimes | bypass d'un floor | P1 |
| QP3-07 | Peut-on réinitialiser une dette en changeant le nom d'une exigence à répétition ? | 1–100 renommages, loi modifiée | échéance d'origine conservée | nouvelle échéance fictive | P0 |
| QP3-08 | Les lectures et écritures de journal peuvent-elles diverger après reprise du même prefix ? | pin ahead, journal behind, interrupted commit | recovery exact | tail forgé | P0 |
| QP3-09 | Un scanner indisponible peut-il masquer un écart plutôt que le laisser visible ? | délai, coverage, perte source | dette/escalade | santé PROVEN | P0 |
| QP3-10 | Une CI fluctuante produit-elle une escalade contrôlée plutôt qu'une boucle de corrections ? | vert/rouge, retries, WorkItems | dette stable et observabilité | réparation infinie occultée | P1 |

## Discipline de lecture

Un test vert n'autorise **aucune conclusion hors de ses hypothèses**. Une suite rouge exige de différencier : bug dans l'oracle, instrumentation, comportement légitime de sécurité, défaut de progression, violation de sûreté. Les contre-expériences ultérieures doivent varier une dimension puis plusieurs, sans transformer ces observations en prescriptions de design.

Lien de suivi des exécutions : https://github.com/ichamafif-svg/NEW/issues/2.

## Mise à jour empirique — 9 octobre 2026

Le run [Actions #45](https://github.com/ichamafif-svg/NEW/actions/runs/37951191335) rapporte cinq expériences long-horizon lisibles et zéro ID signalé. Il s'agit de **cinq séquences de 80 intentions sur des ressources différentes**, et non de la vie d'une obligation sur un même sujet. Ne pas extrapoler de la réussite des 400 tentatives une propriété de convergence ou de liveness d'une maintenance réelle.

Les questions de continuité sur même sujet, expiration et restitution des obligations sont désormais les feuilles O1/R1 prioritaires du [backlog consolidé](P3_DEPTH_COVERAGE_BACKLOG.md). Pour chaque essai suivant, collecter `obligation.subject`, `opened`, `due`, l'empreinte de preuve, l'identité de tentative et le verdict de santé avant/après. Aucune nouvelle abstraction n'est sélectionnée.
