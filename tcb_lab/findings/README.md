# Findings — index chronologique et niveau de preuve

**État de lecture consolidé au 9 octobre 2026.** [Accueil canonique du lab](../README.md) · [Décision actuelle 16/16 K/T/U](../FUNCTIONAL_BOUNDARY_FREEZE_DECISION.md) · [Critères P3 non atteints](../P3_EXIT_CRITERIA.md) · [Registre CI automatique](https://github.com/ichamafif-svg/NEW/issues/2).

## Interprétation des statuts

**OBSERVED** = trace interprétable dans un harnais précis ; **PARSED** = artefact JSON lisible ; **CI success** = pipeline passé ; **CLOSED_CONDITIONAL** = allocation conceptuelle de responsabilités ; **PHYSICALLY_VERIFIED** exigerait des contrôles effectifs de clés, fournisseurs, temps et réseaux sur une installation donnée. Aucun de ces quatre premiers marqueurs ne signifie le cinquième.

## Ordre de lecture recommandé

| Période | Documents | Ce qu'ils apportent | Ce qu'ils ne prouvent pas |
|---|---|---|---|
| Phase III et priorités | [Campagne III](P3_CAMPAIGN_III.md), [priorités](P3_PRIORITY_CAMPAIGN.md), [premiers résultats](P3_PRIORITY_FIRST_RESULTS.md) | Traces adversariales et limites de lecture | Sécurité universelle |
| Approfondissement | [Seconde profondeur](P3_SECOND_DEPTH_CAMPAIGN.md), [résultats](P3_SECOND_DEPTH_RESULTS.md), [horizon long](P3_LONG_HORIZON_QUESTIONS.md) | Contrastes, répétitions, cas historiques | Réseau réel ou anti-rollback physique |
| IV / IV-B | [Campagne IV](P3_CAMPAIGN_IV.md), [revue IV-B](../IVB_BOUNDARY_CLOSURE.md) | Premières allocations conditionnelles K/T/U | Statut actuel des 16 garanties |
| IV-C | [Campagne IV-C](P3_CAMPAIGN_IVC.md), [décision IV-C](../IVC_BOUNDARY_DECISIONS.md) | Instantané 14/2 historique | Qu'il reste actuellement deux allocations non attribuées |
| IV-D | [G08/G16](P3_G08_G16_CAMPAIGN.md), [première interprétation](P3_G08_G16_FIRST_INTERPRETATION.md) | Retraits et tentatives, témoins corrigés | Perte de dette inférée de `state.obligations` vide |
| IV-E / IV-F | [Raisons et plan](P3_G08_G16_PLAN_DIAGNOSTICS.md), [backoff 24 h](P3_G08_G16_IVF_BACKOFF.md), [responsabilité retry](P3_G08_G16_RETRY_ACCOUNTABILITY.md) | Échec de tests, retrait, reprise après backoff | Garantie de progrès global |
| IV-G | [Health et escalade](P3_G08_G16_IVG_HEALTH_ESCALATION.md) | 21 lignes ouvertes, 0 escalade dans la fenêtre observée | Absence d'escalade pour toutes les échéances |
| IV-H | [Obligation canonique](P3_G08_G16_IVH_CANONICAL.md) | `target:vulns` stable en identité, sujet, opened/due sur huit cycles malgré 1→4 propositions | Rollback/réassignation/changement de loi |
| IV-I | [Franchissement de deadline](P3_G16_IVI_DEADLINE.md) | Expérience avant/après due, résultat brut dans les artefacts CI | Une exigence d'escalade non formulée par la loi |
| Vue transversale | [Statut détaillé](P3_LAB_STATUS.md), [registre de preuve](P3_EVIDENCE_REGISTER.md), [constats CI](P3_CI_OBSERVATIONS.md), [changelog](P3_LAB_CHANGELOG.md) | Chronologie et divergences | Certificat de production |

## Conclusions stables à transmettre

**G08** : la responsabilité continue est distincte d'une tentative de réparation. Le noyau doit conserver ouverture et échéance au cours d'un écart continu ; IV-H soutient localement ce comportement. La durabilité physique et la vérité des observations exigent T.

**G16** : le noyau juge dette et exigibilité d'escalade, pas le scheduling. Backoff, retries, stratégie de correction et notification opérationnelle relèvent de U/T sous hypothèses d'équité/disponibilité. La simulation n'établit pas une garantie universelle de progression ni son impossibilité.

**G07/G13** : authenticité cryptographique d'un rapport n'implique pas vérité, couverture ou indépendance des mesures.

**G09/G10/G15** : autorisation logique, absence de chemin privilégié alternatif et effectivité physique d'une exécution sont trois problèmes distincts.

## Archives et règles d'erratum

Les rapports originaux sont conservés, y compris les interprétations dont le contexte a évolué. Les constats de faux témoins ou d'assertions historiques non reproductibles restent visibles ; on les explique plutôt que de les effacer. **La source courante de délimitation est [FUNCTIONAL_BOUNDARY_FREEZE_DECISION.md](../FUNCTIONAL_BOUNDARY_FREEZE_DECISION.md)** ; ce dossier ne remplace pas un audit de l'implémentation `prototype/hybrid-kernel-v1`.
