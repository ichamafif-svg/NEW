# LAB_CHARTER_AND_HANDOFF — mandat, frontière et transfert vers Standard

**9 octobre 2026 — état directeur.** Ce document clarifie le laboratoire, sans changer `SCOPE.md` ni les garanties.

## Mission du lab et produit final

**Standard** vise la création, l'évolution et avant tout la **maintenance autonome continue de dépôts et systèmes logiciels**, y compris BUILD et RUN, avec sécurité, SRE et conformité gouvernées, sans confier la souveraineté à un agent ni à une personne isolée. Standard doit intégrer les capacités existantes de l'entreprise, pas nécessairement recréer son IAM, CI/CD, ses scanners, journaux, orchestrateurs et outils d'incident.

Le **TCB Lab** n'est pas Standard : il formule les propriétés indispensables de confiance, classe leurs responsabilités et conserve des falsificateurs. Il ne développe pas les WorkItems, l'interface, le monitoring ou les connecteurs métier.

## Les trois surfaces

- **K : noyau constitutionnel déterministe** — décide autorité, loi, preuve qualifiée, transitions exhaustives, obligations persistantes et autorisation bornée d'effets. Il ne doit pas exécuter d'opérations métier.
- **T : Trusted External** — mécanismes indispensables à l'effectivité des garanties : identité physique et clés, horloges, ancrages anti-rollback, second jugement réellement indépendant, preuve instrumentée, garde de secrets/egress, readback et livraison conditionnelle des signaux critiques. **Hors du code K ne signifie pas hors TCB effective.**
- **U : système autonome non souverain** — agents, planification, WorkItems, BUILD/RUN, diagnostic, scanners non autorisants, tests et orchestration. Il agit dans des capacités bornées.

## Décisions déjà prises

1. **Scope sémantique figé** : sept responsabilités, [SCOPE.md](SCOPE.md).
2. **Allocation fonctionnelle conditionnelle figée** : G01–G16, [FUNCTIONAL_BOUNDARY_FREEZE_DECISION.md](FUNCTIONAL_BOUNDARY_FREEZE_DECISION.md).
3. **Orientation d'implémentation** : noyau hybride relationnel avec **un seul jugement déterministe**, modèle générique sans « hard mapping » métier. C'est une décision de conception **hors du scope du lab** ; elle ne transforme pas l'inventaire comparatif A/B/C en résultats de benchmark.
4. **Branche d'exécution** : [prototype/hybrid-kernel-v1](https://github.com/ichamafif-svg/NEW/tree/prototype/hybrid-kernel-v1/hybrid_kernel). Documents externes au lab : `KERNEL_CONCEPTUAL_MODEL.md`, `TRUSTED_EXTERNAL_CONTRACTS.md`, `KERNEL_EXECUTION_PROTOCOL.md`, `PRODUCTION_GAP_AND_REUSE.md`. La branche contient des briques réutilisées de `tcb/` et un `ConstitutionalRuntime` transitoire ; **la migration vers un seul cœur hybride générique n'est pas terminée**.
5. **Aucun verdict de disponibilité production**. La branche peut constituer un candidat sérieux, mais autorité intégrée, preuves, ancrages indépendants, garde physique et tests de panne doivent être démontrés avant promotion.

## Frontière d'interprétation

| Question | Où travailler ? | Condition |
|---|---|---|
| Faut-il une responsabilité constitutionnelle supplémentaire ? | Lab, décision écrite et falsificateur | Rouvrir le scope uniquement pour preuve de lacune |
| Comment encoder une règle, relation ou transition ? | Branche prototype | Respect du scope et test de non-régression |
| Quel KMS, IAM, horloge ou pin store exploiter ? | Projet d'intégration T | Contrat et domaine de confiance vérifiés |
| Comment les agents détectent et réparent ? | Standard BUILD/RUN, U | Aucune augmentation de privilège implicite |
| Pourquoi une campagne historique était rouge ? | Lab `findings/` et logs | Trace, oracle, hypothèse, causes distinctes |
| Peut-on déployer ? | Revue de promotion séparée | Gates G01–G16 et T effectifs, pas une CI verte |

## Statuts à ne plus mélanger

- **FUNCTIONAL_BOUNDARY_FROZEN (16/16, conditional)** : le découpage K/T/U est arrêté.
- **IMPLEMENTATION_VERIFIED** : à démontrer pour chaque mécanisme ; non globalement atteint.
- **PHYSICAL_TRUST_VERIFIED** : à démontrer pour chaque installation T ; non atteint globalement.
- **P3_EXIT_PASSED** : **non**.
- **PRODUCTION_READY** : **non**.

Les chiffres 4/12 et 14/2 de IV-B/IV-C sont des états de recherche historiques. Les mots « ouvert » dans leurs sections restent des constats à date, **pas des statuts présents de délimitation**.

## Politique documentaire

La lecture commence par [README.md](README.md), puis [scope](SCOPE.md), [décision de frontière](FUNCTIONAL_BOUNDARY_FREEZE_DECISION.md), [critères de sortie](P3_EXIT_CRITERIA.md) et [findings](findings/README.md). Les anciens plans et protocoles restent archivés en place pour la traçabilité, sans être supprimés ni réécrits comme si l'histoire n'avait pas eu lieu. Une mise à jour de code dans la branche du prototype ne doit pas être présentée dans le lab comme une preuve expérimentale, tant que sa CI ou son audit n'a pas été vérifié.
