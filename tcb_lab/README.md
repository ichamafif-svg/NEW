# Standard — Laboratoire expérimental TCB

**Branche :** `research/tcb-lab-scope-frozen`  
**Base de référence :** `main@d6347dccec714c0193bbc43af5de7e96e3a9ad27`  
**Statut :** laboratoire de recherche, non déployable.

## Mandat exclusif

Recherche sur la **Trusted Computing Base (TCB)** de Standard : noyau déterministe, mécanismes et dépendances de confiance indispensables à ses garanties. **Aucun développement** de produit, agent, orchestration M2, console, dashboard, intégration métier ou nouvelle fonctionnalité de maintenance dans cette branche.

Le code historique de `main` présent dans l'arbre est **un corpus de référence**, non une architecture à conserver. Aucune compatibilité avec les anciens formats, API, journaux, genèses ou modules n'est requise ; chaque garantie démontrée doit toutefois être préservée ou renforcée.

## Ce qui est figé

`SCOPE.md` définit les **sept responsabilités** (Identity, Authority, Law, State, Evidence, Obligation, Effect), les trois périmètres (décision, infrastructure de confiance, autonomie non souveraine), les cinq contrats transversaux, les garanties planchers et les critères de complétude. Le périmètre de responsabilités est figé ; sa complétude reste **à démontrer**.

`RESEARCH_PROTOCOL.md` prescrit la séquence : compléter/valider les garanties et les frontières → campagnes adversariales → inventaire → regroupement des causes racines → recherche de nouvelles abstractions → comparaison rigoureuse → prototype → nouvelle campagne.

## Ce qui demeure libre

Nombre de concepts internes, représentation constitutionnelle, DSL/CIR, algèbre de transitions, moteur de contrats, structure du noyau, langages, modules, protocoles et persistance. **Aucune abstraction n'est privilégiée ou adoptée par défaut.** L'algèbre de transitions essayée sur une autre branche n'est qu'une hypothèse, pas une fondation.

## Règles de laboratoire

- Préserver `main` et la branche `feat/vnext-deterministic-core` : pas de fusion ni modification implicite.
- Regrouper les expériences dans `tcb_lab/experiments/` et leurs résultats dans `tcb_lab/findings/`, avec hypothèse, scénario, procédure reproductible, résultat observé, dépendances et limitation.
- Séparer **OBSERVÉ**, **HYPOTHÈSE**, **NON TESTÉ** et **VALIDÉ**. Une documentation ou un test écrit mais non exécuté ne vaut pas validation.
- Les réductions de taille ne sont pas un objectif autonome : mesurer la TCB effective et les hypothèses externes.
- Ne pas confondre containment provisoire d'une vulnérabilité et correction architecturale.
- Ne pas mapper prématurément les sept responsabilités vers une algèbre ou un IR.
- Les preuves de non-régression doivent être comportementales **et** couvrir les frontières d'effet, de temps, de stockage, de preuve et de déploiement.

## Portes

**G0 — Scope fixé : OUI (contrat de responsabilités).**  
**G1 — Complétude démontrée : NON.**  
**G2 — Recherche adversariale exhaustive : NON.**  
**G3 — Causes racines consolidées : NON.**  
**G4 — Choix d'abstraction : INTERDIT avant G1–G3.**  
**G5 — Noyau candidat validé : NON.**

Le but est de découvrir **la meilleure abstraction pour satisfaire les garanties**, non de réécrire l'existant avec d'autres noms.

## Phase 3 — campagne active (9 octobre 2026)

Plan complet des huit phases : [PLAN.md](PLAN.md). Inventaire des garanties : [GUARANTEE_MATRIX.md](GUARANTEE_MATRIX.md). Hypothèses de menace : [THREAT_MODEL.md](THREAT_MODEL.md). Campagne adversariale, scénarios et limites : [ATTACK_CATALOG.md](ATTACK_CATALOG.md).

Les suites `experiments/p3_signed_core.py` et `experiments/p3_effect_line.py` fournissent **12 exercices adversariaux** (huit sur les décisions signées et quatre sur les frontières d'effet). Les scénarios complémentaires du catalogue exigent encore des harness dédiés, notamment pour multi-hôte, fournisseur et restauration. `python tcb_lab/experiments/g1_decision_probes.py` constitue une première expérience de scope additionnelle.

Une CI lecture seule `.github/workflows/tcb-lab-p3.yml` exécute ces suites sur un environnement isolé sans clés Standard ni droit d'écriture. **Aucun succès d'exécution n'est revendiqué tant que les logs ne sont pas vérifiés.** Les résultats sont distingués des hypothèses de lecture de code. Les phases 1–2 restent ouvertes à l'affinement, la phase 3 est en cours et **aucune abstraction centrale n'a été adoptée**.

## Phase 3 — extension adversariale à grande échelle

La campagne possède désormais [80 nouvelles hypothèses structurées](ATTACK_EXPANSION.md) en plus des [24 scénarios initiaux](ATTACK_CATALOG.md), soit **104 hypothèses d'attaque distinctement répertoriées**. Trois axes de tests supplémentaires sont ajoutés : `experiments/p3_mutation_fuzz.py` (**30 mutations signées**), `experiments/p3_autonomy.py` (**10 expériences autorité/progrès**), et le [modèle de menace de l'autonomie](AUTONOMY_THREAT_MODEL.md).

Au total, **52 exercices locaux sont codés dans les quatre scripts P3** : huit entrées signées, quatre effets locaux, trente mutations et dix expériences sur l'autonomie. Les quatre expériences G1 restent séparées. Les hypothèses non codées restent une file de recherche, et non des résultats. La CI déclenche ces suites sur push. L'accès GitHub disponible ici ne fournit pas encore de compte rendu d'exécution validé : **aucun résultat vert ni vulnérabilité confirmée n'est annoncé**.

L'objectif de Standard est l'**autonomie gouvernée**, pas seulement le refus de toute action : chaque campagne doit examiner si un agent habilité peut progresser en respectant les protections, et si toute impossibilité de progresser devient un état, une obligation ou une escalade explicite. Le noyau ne devient pas pour autant le scheduler ou l'agent.

## Phase 3 — profondeur bloquante, pas course au volume

La nouvelle [P3_EXIT_CRITERIA.md](P3_EXIT_CRITERIA.md) définit huit **portes de clôture obligatoires**. La [COVERAGE_DEPTH.md](COVERAGE_DEPTH.md) rend visibles les trous entre les seize familles de garanties et les cinq dimensions : décision, composition, panne, confiance physique et progression autonome. Chaque cellule `Coded` reste distincte d'un résultat exécuté.

`experiments/p3_compositions.py` ajoute **sept séquences adversariales composées** sur les restrictions, les jetons, les effets inconnus, les preuves et la continuité du travail légitime. La CI inclut ces séquences. Cela porte le laboratoire à **59 exercices P3 codés**, toujours **non validés par un run observé**. Les hypothèses recensées restent au nombre de 104 ; les exercices ne correspondent pas nécessairement un-pour-un aux hypothèses.

**La phase 3 demeure ouverte jusqu'à satisfaction des portes, pas jusqu'à un quota arbitraire de tests.** Le moteur d'autonomie reste extérieur au noyau constitutionnel, mais tout mécanisme autorisant ou clôturant ses effets doit être éprouvé dans la frontière de confiance.

## Phase 3 — recherche ouverte (pas de design)

[P3_EXPLORATION_PROTOCOL.md](P3_EXPLORATION_PROTOCOL.md) formalise la boucle **observation → question → hypothèses alternatives → contre-expérience → nouvelles questions**. Les résultats ne déclenchent ni refonte du scope ni choix d'abstraction. `experiments/p3_counterexperiments.py` ajoute cinq expériences couplées opposant perturbation hostile et voie de progression légitime, désormais incluses dans la CI et le registre automatique GitHub issue #2. Cela donne **64 expériences P3 codées**, plus les quatre G1. Toute interprétation doit rester conditionnelle aux traces effectivement observées.

## Phase 3 — observation approfondie sur durée (9 octobre 2026)

Le nouveau harnais `experiments/p3_long_horizon.py` soumet le journal de référence à **5 séquences reproductibles de 80 tentatives** (400 transitions candidates), en alternant requêtes légitimes et adversariales ; chaque séquence vérifie le refus des entrées incorrectes et la progression des intents autorisées. Ce test **ne** dispatch pas d'effet physique et ne prouve aucune garantie de liveness universelle.

Le [registre Actions automatique](https://github.com/ichamafif-svg/NEW/issues/2) a publié, pour le run de laboratoire `37950062059`, **8 suites P3, 69 exercices** (8+4+30+10+7+5+5) et quatre G1, tous avec JSON analysable et zéro ID signalé. Les cinq expériences long-horizon ont effectivement été exécutées ; cela ne ferme aucun gate de la phase 3. Le [journal des questions nouvelles](findings/P3_LONG_HORIZON_QUESTIONS.md) décrit les dix expérimentations plus profondes qui restent nécessaires, en particulier les multi-hôtes, le changement de loi en cours de départ et la persistance des dettes.

La règle de [P3_EXPLORATION_PROTOCOL.md](P3_EXPLORATION_PROTOCOL.md) demeure : **explorer et poser de nouvelles questions, jamais modifier le scope ou choisir une abstraction en phase 3**.

## Phase 3 — arbre d'expériences PROFONDEUR × COUVERTURE

[EXPERIMENT_TREE_DEPTH_COVERAGE.md](EXPERIMENT_TREE_DEPTH_COVERAGE.md) est désormais la structure directrice de l'exploration : **8 branches de couverture**, **8 profondeurs D0–D7**, quatre sous-arbres P0 illustrés, oracles safety/progression et exigences de preuve par feuille. Les résultats verts et rouges ouvrent des **enfants expérimentaux** ; ils ne servent pas à redéfinir le scope, réparer le cœur ou préchoisir un modèle. La profondeur effective doit être attribuée sur preuves de run, pas sur la seule présence de fichiers.

## Documentation findings consolidée — 9 octobre 2026

La porte d'entrée empirique est maintenant [findings/README.md](findings/README.md). Elle relie le [midpoint](findings/P3_MIDPOINT.md), les [preuves et runs précis](findings/P3_EVIDENCE_REGISTER.md), les [erreurs de mesure et rouges historiques](findings/P3_CI_OBSERVATIONS.md), la [limite des séries longues](findings/P3_LONG_HORIZON_QUESTIONS.md) et le [backlog profondeur × couverture](findings/P3_DEPTH_COVERAGE_BACKLOG.md). Les paragraphes de statut plus anciens du présent README reflètent des étapes historiques de rédaction ; privilégier le registre de preuves daté pour le statut réellement observé.

**Suite suggérée par les findings :** reproduire et départager l'échec du retrait de réparation (O1/R1), puis ouvrir les contre-expériences sur effet incertain et fausse preuve. Les résultats servent à poser des questions plus difficiles, pas à modifier la constitution, le scope ou l'abstraction.

## État actuel — campagne adversariale III (2026-10-09)

**Point d'entrée à privilégier :** [findings/P3_LAB_STATUS.md](findings/P3_LAB_STATUS.md). Le [nouvel arbre expérimental vivant](EXPERIMENT_TREE_DEPTH_COVERAGE.md) lie les huit branches de couverture aux niveaux D0–D7, et chaque observation à ses hypothèses/contre-expériences. La [campagne III](findings/P3_CAMPAIGN_III.md) cible les trois findings dominants : refus anti-replay masqué par `HIST.TIME`, variabilité de sujets après `withdrawn`, et preuve signée sans accès à la vérité extérieure. Trois nouveaux scripts (8 + 18 + 6 scénarios) sont raccordés à GitHub Actions et au [registre automatique #2](https://github.com/ichamafif-svg/NEW/issues/2). Les résultats ne servent qu'à **explorer** : aucune conclusion sur l'abstraction ni modification de la TCB.

## Campagne IV — délimitation empirique accélérée

La [matrice des frontières K/T/U](TCB_BOUNDARY_MATRIX.md) classe les 16 garanties sans exclure de la *TCB effective* les mécanismes de confiance extérieurs. [ESTABLISHED_LIMITS.md](ESTABLISHED_LIMITS.md) distingue impossibilités logiques conditionnelles et frontières physiques encore ouvertes. [SCOPE_FREEZE_REVIEW.md](SCOPE_FREEZE_REVIEW.md) précise ce qui est figé dans le contrat sémantique existant et ce qui **n'est pas encore prouvé**. Des discriminants locaux `p3_iv_boundary_probes.py` ont été ajoutés au workflow ; leur observation réelle doit être vérifiée dans le registre [issue #2](https://github.com/ichamafif-svg/NEW/issues/2).

## IV-B — revue des frontières et critères de fermeture

La [revue IV-B](IVB_BOUNDARY_CLOSURE.md) classe séparément les frontières `CLOSED_CONDITIONAL`, `OPEN_CRITICAL` et `OPEN_SEMANTIC` pour **G01–G16**, avec les contre-exemples et dépendances physiques. Quatre nouvelles expériences signées (effet révoqué, retry inconnu, preuve bon/mauvais sujet) sont intégrées à la CI via `p3_ivb_boundary_pairs.py`. **La classification ne constitue pas une validation de sûreté ; aucun scope ou noyau n'a été modifié.**

## Campagne IV-C — conclusion de délimitation (pas une preuve physique)

[IVC_BOUNDARY_DECISIONS.md](IVC_BOUNDARY_DECISIONS.md) passe en revue les **12 frontières antérieurement ouvertes** : dix allocations K/T/U deviennent **conditionnelles** sur la base de leurs contrats d'information et d'application ; **G08** (continuité des obligations) et **G16** (progression autonome) restent sémantiquement ouvertes. Avec les quatre allocations déjà conditionnelles en IV-B, on obtient **14 délimitations conditionnelles / 2 ouvertes**, *et non 14 garanties vérifiées*. Les contrats externes restent non validés physiquement. `p3_ivc_scope_audit.py` vérifie seulement la cohérence documentaire dans la CI, sans se substituer aux expériences adversariales manquantes. Aucun changement du scope sémantique [SCOPE.md](SCOPE.md) ou du noyau.

## Consolidation IV-D — G08 / G16 (2026-10-09)

Pour l'état actualisé, voir le [journal de consolidation](findings/P3_LAB_CHANGELOG.md), la [campagne G08/G16](findings/P3_G08_G16_CAMPAIGN.md) et le [registre des runs](https://github.com/ichamafif-svg/NEW/issues/2). Les nouvelles expériences opposent 20 cycles de dégradation persistante, 20 cycles avec signal de guérison et 20 cycles de contrôle sain ; `G08` et `G16` restent ouvertes tant que dette canonique/échéance et progrès conditionnel ne sont pas démontrés.

## Décision de consolidation — 9 octobre 2026 (statut actuel du **découpage**)

La [décision canonique de frontière fonctionnelle](FUNCTIONAL_BOUNDARY_FREEZE_DECISION.md) attribue désormais **16/16 garanties G01–G16 à K (décisions du noyau), T (Trusted External) et U (autonomie remplaçable)** sous hypothèses explicites. **Statut : CONDITIONAL_BOUNDARY_FROZEN**, et **non** 16 garanties prouvées. Les anciennes mentions `14 conditionnelles / 2 ouvertes` ou `OPEN_SEMANTIC` pour G08/G16 décrivent **l'étape IV-C/IV-D historique** et sont supplantées **uniquement pour la délimitation fonctionnelle** ; elles restent utiles comme état des preuves à leur date. G08 : dette canonique indépendante des tentatives ; G16 : règles de permission, dette et exigibilité d'escalade dans K, scheduling/retries/notification dans U et préconditions fiables dans T. La campagne IV-I et les travaux d'implémentation ne bloquent **pas** la décision de découpage. Le scope sémantique `SCOPE.md` demeure intact ; l'assurance physique, l'audit de déploiement et les portes de sortie P3 restent **ouverts**. Ne pas relancer une boucle de recherche sur tout Standard sans contre-exemple démontrant une mauvaise attribution K/T/U.
