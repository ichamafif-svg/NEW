# STANDARD — Architecture canonique

**Statut : architecture cible validée au niveau conceptuel.** Ce document définit Standard en tant que produit et système, sans dépendance à une implémentation particulière. **Architecture validée ≠ conformité ou sûreté de production démontrée.** Les contrats d'exploitation doivent encore être éprouvés par des tests et un déploiement contrôlé.

## Mission

Standard est une plateforme **AI-native** destinée à **créer, faire évoluer et surtout maintenir continuellement** des systèmes logiciels par des agents autonomes, sans accorder de confiance souveraine à l'agent, à un individu isolé ou à un composant isolé.

L'agent peut proposer, diagnostiquer, tester et corriger ; **seule la décision constitutionnelle** détermine ce qui est admissible. Les opérations réelles restent soumises à des frontières de confiance explicites.

## Produit : BUILD et RUN

**BUILD** crée ou transforme les systèmes : conception, code, vérifications, intégration, déploiement gouverné. Une application peut commencer presque de zéro. **RUN** observe activement la production et le dépôt, détecte les écarts, corrige, vérifie, surveille la sécurité, la disponibilité, la conformité et l'évolution. BUILD et RUN sont deux contextes d'un **même système d'autonomie**, pas deux autorités ni deux constitutions.

La maintenance autonome continue est le cœur du produit : écart entre exigences et réel → obligation durable → planification et exécution par agents → vérification indépendante → clôture ou escalade. Le travail peut prendre la forme de WorkItems, mais une obligation constitutionnelle ne se confond pas avec un ticket, un essai ou un agent.

## Architecture en quatre niveaux

1. **Surface produit** : état de santé, couverture, autonomie, risques, obligations, escalades et décisions humaines. Les empreintes et protocoles restent accessibles pour l'audit, non comme UX principale.
2. **Autonomie non souveraine (U)** : agents, WorkItems, workflows BUILD/RUN, scanners, observabilité, diagnostics, planification, réconciliation opérationnelle et adaptateurs aux outils existants. U propose et agit uniquement sous autorisations ; U ne définit pas la loi.
3. **Noyau constitutionnel hybride (K)** : un jugement déterministe unique sur identité, autorité, loi, état, preuves, obligations et effets. Il évalue des contraintes typées, dérive les conséquences obligatoires et prononce un delta atomique. Pas de mapping métier codé en dur ni de deuxième autorité.
4. **Trusted External (T)** : capacités indispensables dans le monde réel : identité/clé, horloge, ancrage durable, qualification des preuves, indépendance des vérificateurs, protection des secrets et des effets, réconciliation et progression vérifiable. Les T font partie de la **TCB effective** bien qu'ils soient hors du noyau pur.

K et T forment une frontière de confiance cohérente ; U n'est jamais un substitut à cette frontière. Les entreprises peuvent réutiliser IAM, CI/CD, cloud, catalogues, scanners, monitoring, gestion d'incidents et plateformes existantes **si leurs contrats vérifiables sont suffisants** ; Standard évite leur remplacement systématique.

## Constitution et autonomie

- **FLOOR-0** protège les fondations de la confiance ; les **floors** de la release imposent les garanties communes.
- La **loi client** relie ces exigences à son contexte et peut ajouter ou durcir, jamais affaiblir les floors.
- Un acteur seul ne peut élargir son autorité. Les changements sensibles utilisent la gouvernance applicable : quorum d'humains distincts, témoins et délais lorsqu'exigés.
- Restriction, révocation et gel suivent leurs règles immédiates ; les mécanismes de déblocage ne constituent pas un god mode.
- Les autorisations sont bornées par sujet, ressource, opération, contexte et durée ; leur délégation doit être atténuante.
- Une preuve n'est recevable qu'avec provenance, qualification, couverture, fraîcheur et indépendance adaptées à l'exigence.
- Les obligations survivent aux retries, renommages de tickets et échecs ; leur clôture nécessite une preuve admissible.
- Aucun effet privilégié n'est présumé accompli parce qu'une décision l'a autorisé : départ contrôlé, réservation, accusé et état `UNKNOWN` si nécessaire.

## Noyau hybride : principe et modèle

La conception est **hybride relationnelle à jugement unique** : relations typées, contraintes finies et conséquences/transactions déterministes dans une seule sémantique. Le modèle de données est extensible pour les domaines métiers ; la sémantique des primitives constitutionnelles est fermée, versionnée et non redéfinissable par un adaptateur.

Le noyau ne connaît pas les notions particulières d'un fournisseur, dépôt, scanner ou outil SRE. Il connaît des principaux, ressources, capacités, lois, faits, obligations, transitions et intentions d'effets. Les connecteurs exposent ces informations selon des contrats gouvernés sans pouvoir fabriquer eux-mêmes une preuve constitutionnelle.

Le noyau doit rester **minimal en mécanismes, complet dans son domaine constitutionnel et invisible dans les opérations ordinaires**. Une capacité limitée et contrôlée permet de travailler sans faire remonter chaque calcul, lecture, scan ou proposition technique dans K ; tout élargissement de pouvoir, mutation constitutionnelle ou effet sensible reste soumis au jugement adéquat.

## Protocole de bout en bout

`proposer → authentifier / qualifier → juger → vérifier lorsque requis → committer atomiquement → réserver / contrôler l'effet → exécuter ou marquer UNKNOWN → réconcilier → auditer / maintenir les obligations`.

Le commit doit être lié au préfixe constitutionnel authentique. L'effet est lié à une destination et à des octets exacts ; un effet autorisé mais non parti peut être bloqué par une restriction plus récente. Les hypothèses d'indépendance et de disponibilité des Trusted External doivent être exposées, pas simplement présumées.

## Frontière de confiance et garanties

Les responsabilités sont réparties entre **K** (prononce les conséquences légales), **T** (rend fiables les prémisses et effets physiques), **U** (réalise le travail). Il ne suffit pas de signer une affirmation `allowed` pour établir une autorité ; K dérive les droits de la constitution et de l'état authentique. Il ne suffit pas non plus de conserver un journal pour rendre impossible sa restauration : l'ancrage doit être indépendant de son domaine de restauration.

## Documents normatifs de cette architecture

- [Contrats d'implémentation par composant](IMPLEMENTATION_CONTRACTS.md) : prescriptions K/T/U, propriétés de refus, couverture G01–G16 et scénarios de réception.
- [Modèle conceptuel du noyau](hybrid_kernel/KERNEL_CONCEPTUAL_MODEL.md) : objets et invariants de K.
- [Contrats Trusted External](hybrid_kernel/TRUSTED_EXTERNAL_CONTRACTS.md) : capacités T, menaces et obligations d'intégration.
- [Protocole d'exécution](hybrid_kernel/KERNEL_EXECUTION_PROTOCOL.md) : séquence atomique et gestion des effets.
- [Présentation du noyau](hybrid_kernel/README.md) : principes et limites de validation.

Ces documents doivent pouvoir être lus sans connaître l'histoire du projet. Toute proposition d'implémentation se mesure à ces contrats ; les tests et preuves de production ne sont pas remplacés par la documentation.

## Critères de validation avant production

Une release ne devient exploitable que lorsque les invariants et les responsabilités K/T/U sont vérifiés, que les tests adversariaux et de concurrence passent, que les hypothèses physiques des T sont prouvées pour le déploiement réel, que la performance est bornée et que les limites de couverture sont explicitement visibles aux utilisateurs. **Aucune déclaration de production-ready n'est implicite dans cette spécification.**
