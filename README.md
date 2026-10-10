# Standard

**Plateforme AI-native de création et surtout de maintenance autonome des systèmes logiciels, sans pouvoir souverain accordé aux agents.**

- **BUILD** : créer, modifier et vérifier les applications.
- **RUN** : surveiller, maintenir, réparer et traiter continuellement les écarts de sécurité, fiabilité et conformité.
- **K — Noyau hybride** : un jugement constitutionnel déterministe unique, sans mapping métier rigide.
- **T — Trusted External** : rendre effectives les garanties physiques (identités, preuves, journal, effets).
- **U — Autonomie** : agents, WorkItems, outils et intégrations existantes ; jamais de pouvoir constitutionnel.

**Cycle central :** écart → obligation durable → travail autonome → preuve qualifiée → clôture ou escalade.

## Lire Standard

1. **[STANDARD_ARCHITECTURE.md](STANDARD_ARCHITECTURE.md)** — vision produit, noyau hybride, frontières de confiance et protocole.
2. **[IMPLEMENTATION_CONTRACTS.md](IMPLEMENTATION_CONTRACTS.md)** — spécification opérationnelle de chaque composant K/T/U, garanties G01–G16 et critères de réception.

Ces deux documents sont autonomes et définissent la cible de conception. **Leur existence ne prouve pas que l'implémentation est prête pour la production.**

## Implémentation du noyau

Un seul interpréteur constitutionnel : `hybrid_kernel.Kernel`. Relations typées, contraintes positives bornées et transitions à delta exhaustif partagent le même jugement. Constitution, quorum, révocation, qualification des preuves, obligations et effets restent gouvernés par ce chemin. Les ressources et instruments sont déclarés dans la loi ; aucun adaptateur ne fournit un `allowed` souverain.

`make check` vérifie les budgets et exécute les régressions constitutionnelles, les tests d'intégration, les transitions relationnelles et les scénarios de dette/preuve. Le budget K inclut les primitives réutilisées ; les composants de confiance physiques et le contrôle indépendant restent comptés séparément dans la TCB effective.

Les Trusted Externals restent à qualifier indépendamment pour chaque déploiement. Le manifeste conserve une release **BLOCKED** tant que leurs critères ne sont pas vérifiés. Les pins d'une autre release ne sont jamais migrés ou réinitialisés silencieusement.

`standard.StandardService` relie désormais une installation `GovernedDeployment` à une vue unique des obligations et des routes de travail BUILD/RUN. Il reprend la loi effective au préfixe courant, distingue route disponible, absence de route, revue humaine et T indisponible, puis transmet seulement des propositions déjà signées à l'admission K/T. `standard.WorkEngine` conserve les tentatives opérationnelles et leurs reprises sans fermer de dette à la place du noyau. Ils n'ont ni secret fournisseur ni port d'effet propre. Cette intégration logicielle ne provisionne pas les T physiques, n'installe pas d'agent autonome et ne rend pas encore M2 équivalent à ce service ; voir [standard/README.md](standard/README.md).
