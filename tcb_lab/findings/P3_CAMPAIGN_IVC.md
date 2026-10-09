# Phase 3 — Campagne IV-C : état des observations et décisions

**Objectif :** trancher au niveau des responsabilités, non prouver que des mécanismes physiques existent déjà. Le [contrat SCOPE.md](../SCOPE.md) n'est pas modifié.

## Travail remis dans cette itération

- [IVC_BOUNDARY_DECISIONS.md](../IVC_BOUNDARY_DECISIONS.md) expose une **hypothèse de frontière pour chacun des douze anciens bloqueurs**, avec le falsificateur et la dépendance physique qu'elle imposerait.
- **Dix frontières sont délimitables conditionnellement par raisonnement sur les capacités du noyau pur** : G02, G05, G07, G09, G10, G11, G12, G13, G14, G15. Elles restent **NON PROUVÉES** dans un déploiement.
- Les deux **questions sémantiques ouvertes** sont G08 (identité et durée d'une même obligation à travers réparations/renommages) et G16 (progrès, équité, arrêt et escalade d'une maintenance autorisée).
- **IV-C scope audit** `p3_ivc_scope_audit.py` vérifie seulement les douze lignes, leurs contradictions et la conservation des blocages ; un succès n'est pas une garantie.
- **IV-C same-target** `p3_ivc_same_target.py` observe 12 cycles d'un même dépôt dégradé avec `found:1` et 12 avec `none`, les sujets, leur état et les obligations visibles. Il ne démontre pas à lui seul le modèle de dette historique.
- Les deux scripts sont connectés au workflow, qui retient leurs JSON et les signale dans l'[issue #2](https://github.com/ichamafif-svg/NEW/issues/2).

## Pourquoi ce n'est pas encore un « scope validé »

La répartition K/T/U peut être logiquement expliquée tout en étant insuffisamment précise sur la continuité d'une dette et l'autonomie sans acteur souverain. Et le terme **EXTERNAL_REQUIRED** ne dispense pas de démontrer la protection physique des secrets, du départ, des pins ou des observations indépendantes. Ces propriétés restent dans la TCB **effective**, même lorsqu'elles ne sont pas calculées par le noyau pur.

## Lecture du résultat

Le bilan **14 délimitations conditionnelles + 2 sémantiques ouvertes** est un *résultat de classification sous hypothèses*, pas « 14 garanties prouvées ». Les résultats de ces scripts restent `CODED_NOT_OBSERVED` jusqu'à lecture d'une exécution CI associée à ce commit ou ses descendants. Si le prochain run est rouge, isoler la cause dans l'instrumentation avant d'inférer un bug TCB.

## Prochains contre-exemples minimaux

1. **G08** : même écart après 20/100 retraits, ouvert/dû exacts malgré changement d'identité de réparation et de commit ; contrôle gap définitivement disparu.
2. **G16** : sous hypothèses de disponibilité et de scheduler équitable, action permise menant à résolution ou escalade bornée ; sinon témoin d'impossibilité explicite.
3. **G02/G09/G10/G15** : processus et credentials séparés, crash après send et avant ACK, observation indépendante du fournisseur.
4. **G05/G07/G11/G12/G13/G14** : collusion physique des clés, oracle commun faux et reprise simultanée journal+pins.
