# Standard TCB Lab — état canonique et mode de lecture

**État consolidé au 9 octobre 2026.** Ce fichier est le **point d'entrée** du laboratoire. Le lab conserve preuves, hypothèses et décisions de frontières ; la construction du nouveau noyau se fait **hors de cette branche**.

## Résumé exécutable en cinq phrases

1. [SCOPE.md](SCOPE.md) fige **sept responsabilités sémantiques** du noyau : Identity, Authority, Law, State, Evidence, Obligation, Effect. Ce n'est ni une architecture de modules ni une preuve de sûreté.
2. [FUNCTIONAL_BOUNDARY_FREEZE_DECISION.md](FUNCTIONAL_BOUNDARY_FREEZE_DECISION.md) fige **16/16 allocations fonctionnelles conditionnelles** G01–G16 entre K (jugement déterministe), T (Trusted External, inclus dans la TCB effective) et U (travail autonome remplaçable).
3. **16/16 ne signifie pas 16 garanties physiquement vérifiées.** L'assurance empirique, les propriétés de déploiement et les gates de la phase 3 restent ouverts. Lire [P3_EXIT_CRITERIA.md](P3_EXIT_CRITERIA.md) et [ESTABLISHED_LIMITS.md](ESTABLISHED_LIMITS.md).
4. Les campagnes IV-F à IV-I observent l'identité stable de `target:vulns` dans IV-H, des retries et des horizons temporels, sans preuve universelle d'escalade/progression ; consulter [l'index des constats](findings/README.md).
5. **La comparaison A/B/C décrite dans [ARCHITECTURE_CAMPAIGN_V.md](ARCHITECTURE_CAMPAIGN_V.md) est historique, non la roadmap active.** Le choix produit est un noyau hybride avec jugement déterministe unique, sans mappage métier imposé. Sa conception et son implémentation candidate sont sur [`prototype/hybrid-kernel-v1`](https://github.com/ichamafif-svg/NEW/tree/prototype/hybrid-kernel-v1/hybrid_kernel).

## Navigation par intention

| Je cherche… | Document de référence | Statut |
|---|---|---|
| La finalité de Standard et la place du lab | [LAB_CHARTER_AND_HANDOFF.md](LAB_CHARTER_AND_HANDOFF.md) | Actuel |
| Les responsabilités constitutionnelles et exclusions | [SCOPE.md](SCOPE.md) | Figé |
| L'allocation **actuelle** des G01–G16 | [FUNCTIONAL_BOUNDARY_FREEZE_DECISION.md](FUNCTIONAL_BOUNDARY_FREEZE_DECISION.md) | Figée **conditionnellement** |
| La table K/T/U détaillée et les falsificateurs | [TCB_BOUNDARY_MATRIX.md](TCB_BOUNDARY_MATRIX.md) | Matrice de travail ; décision canonique prioritaire |
| Les garanties et niveaux de preuve | [GUARANTEE_MATRIX.md](GUARANTEE_MATRIX.md) et [ESTABLISHED_LIMITS.md](ESTABLISHED_LIMITS.md) | Hypothèses explicites |
| Les expériences et leurs fichiers | [EXPERIMENT_TREE_DEPTH_COVERAGE.md](EXPERIMENT_TREE_DEPTH_COVERAGE.md) et [ATTACK_CATALOG.md](ATTACK_CATALOG.md) | Archives vivantes |
| Ce qui a réellement été observé | [findings/README.md](findings/README.md) | Index chronologique |
| Les critères empêchant une promotion | [P3_EXIT_CRITERIA.md](P3_EXIT_CRITERIA.md) | **Non remplis** |
| La conception et le code du noyau hybride | [branche prototype](https://github.com/ichamafif-svg/NEW/tree/prototype/hybrid-kernel-v1/hybrid_kernel) | Hors lab ; non production-ready |
| L'historique CI brut | [Registre automatique #2](https://github.com/ichamafif-svg/NEW/issues/2) | Instantané régénéré à chaque run |

## Hiérarchie documentaire

**Normatif de périmètre :** `SCOPE.md` → `FUNCTIONAL_BOUNDARY_FREEZE_DECISION.md` (allocation) → `P3_EXIT_CRITERIA.md` (niveau de preuve et gates).

**Observations :** rapports `findings/`, artefacts des expériences et logs CI, qui ne peuvent jamais contredire silencieusement une norme : ils doivent enregistrer un contre-exemple puis demander une décision explicite.

**Historique conservé :** `IVB_BOUNDARY_CLOSURE.md` (4 conditionnelles / 12 ouvertes à l'époque), `IVC_BOUNDARY_DECISIONS.md` (14/2 à l'époque), `SCOPE_FREEZE_REVIEW.md`, `PLAN.md`, `RESEARCH_PROTOCOL.md` et `ARCHITECTURE_CAMPAIGN_V.md`. Leur terminologie « ouvert », « à sélectionner » ou « en cours » est **datée**, sauf élément repris expressément par la présente synthèse.

## Décisions G08/G16 et règle d'arrêt

**G08** : le noyau possède la continuité canonique de l'obligation et ses conditions de clôture. Le retry/WorkItem appartient à U ; la durabilité et la fiabilité des observations à T. IV-H constate localement une obligation stable sur huit cycles malgré quatre propositions. **Ce n'est pas une preuve contre un rollback coordonné ou un changement de sujet.**

**G16** : le noyau détermine obligations, permissions et exigibilité d'escalade selon la loi ; progression effective, scheduling, retries et livraison physique sont conditionnels à T/U. Une absence de progression sans disponibilité/fairness ne démontre pas automatiquement un défaut de K.

**Stop-rule** : ne pas rouvrir une frontière fonctionnelle pour enquêter sans fin sur les scanners, WorkItems, agents et backoffs. Rouvrir seulement sur un contre-exemple mettant en évidence un devoir constitutionnel non attribué ou une contradiction K/T/U prouvée. Les investigations opérationnelles continuent dans les audits d'implémentation et de déploiement.

## Règles de conservation

- Pas de réécriture rétroactive des rapports expérimentaux ; rectification sous forme de note datée/erratum.
- Pas de modification du noyau historique, des floors ou du scope par une campagne documentaire.
- Ne jamais transformer `OBSERVED`, `PARSED`, CI green ou `CLOSED_CONDITIONAL` en attestation de sûreté.
- Les documents de la branche hybride ne peuvent pas « valider » les Trusted External par déclaration ; ils doivent citer des tests et conditions réelles de déploiement.
