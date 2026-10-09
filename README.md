# Standard

**Plateforme AI-native pour créer, faire évoluer et surtout maintenir des systèmes logiciels en autonomie, sans donner de pouvoir souverain aux agents.**

**[Lire l'architecture canonique de Standard](STANDARD_ARCHITECTURE.md)**

## Promesse produit

Standard orchestre des agents qui détectent les écarts, réalisent les évolutions, corrigent les défaillances et vérifient les résultats. L'autonomie est bornée par une constitution déterministe et des frontières de confiance vérifiables. Les décisions humaines n'interviennent que lorsqu'elles sont réellement exigées par l'autorité applicable.

- **BUILD** : construire, transformer, tester et intégrer des systèmes logiciels.
- **RUN** : observer continuellement, diagnostiquer, réparer, faire évoluer et maintenir la sécurité, la fiabilité et la conformité.
- **Gouvernance** : floors non affaiblissables, loi client plus stricte, autorité contrôlée, preuves indépendantes, obligations durables et effets privilégiés protégés.
- **Intégration** : réutiliser les services IAM, CI/CD, monitoring, cloud et outils de conformité existants lorsque leurs garanties sont suffisantes.
- **Expérience humaine** : montrer ce qui est couvert, ce qui ne l'est pas, les risques, les obligations ouvertes, les résultats et les décisions attendues.

## Architecture

**K — noyau constitutionnel hybride** : modèle relationnel typé, contraintes et conséquences dans un seul jugement déterministe. Il gouverne Identity, Authority, Law, State, Evidence, Obligation et Effect sans mapping métier figé.

**T — Trusted External** : identité physique et clés, release pin, temps, ancrages durables, vérification indépendante, qualification des preuves, egress privilégié, réconciliation et acheminement des escalades. Ils sont dans la frontière de confiance effective.

**U — autonomie non souveraine** : agents, WorkItems, diagnostics, observabilité, planification, workflows BUILD/RUN et adaptateurs. Ils accomplissent le travail sans pouvoir contourner K/T.

La maintenance suit le cycle : **écart → obligation → travail autonome → preuve admissible → clôture ou escalade**.

## Documentation canonique

| Document | Objet |
|---|---|
| [STANDARD_ARCHITECTURE.md](STANDARD_ARCHITECTURE.md) | Produit Standard, architecture générale et garanties |
| [KERNEL_CONCEPTUAL_MODEL.md](hybrid_kernel/KERNEL_CONCEPTUAL_MODEL.md) | Primitives, relations et jugement déterministe |
| [TRUSTED_EXTERNAL_CONTRACTS.md](hybrid_kernel/TRUSTED_EXTERNAL_CONTRACTS.md) | Contrats de confiance physiques |
| [KERNEL_EXECUTION_PROTOCOL.md](hybrid_kernel/KERNEL_EXECUTION_PROTOCOL.md) | Admission, commit, effets et reprise |
| [hybrid_kernel/README.md](hybrid_kernel/README.md) | Vue synthétique du noyau |

Ces documents forment la **spécification autonome de l'architecture cible**. Ils ne doivent pas être lus comme une déclaration de conformité de l'implémentation courante. La mise en production nécessite des preuves d'implémentation, d'indépendance des composants de confiance, de résistance aux pannes et de performance.

## État

**Architecture conceptuelle définie ; qualification de production non acquise.** Les systèmes externes et les effets privilégiés doivent être vérifiés dans leur environnement physique de déploiement.
