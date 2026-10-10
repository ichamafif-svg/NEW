# STANDARD — Architecture canonique

**Statut : architecture cible validée au niveau conceptuel.** Ce document définit Standard en tant que produit et système, sans dépendance à une implémentation particulière. **Architecture validée ≠ conformité ou sûreté de production démontrée.** Les contrats d'exploitation doivent encore être éprouvés par des tests et un déploiement contrôlé.

## Mission

Standard est une plateforme **AI-native** destinée à **créer, faire évoluer et surtout maintenir continuellement** des systèmes logiciels par des agents autonomes, sans accorder de confiance souveraine à l'agent, à un individu isolé ou à un composant isolé.

L'agent peut proposer, diagnostiquer, tester et corriger ; **seule la décision constitutionnelle** détermine ce qui est admissible. Les opérations réelles restent soumises à des frontières de confiance explicites.

## Produit : BUILD et RUN

**BUILD** crée ou transforme les systèmes : conception, code, vérifications, intégration, déploiement gouverné. Une application peut commencer presque de zéro. **RUN** observe activement la production et le dépôt, détecte les écarts, corrige, vérifie, surveille la sécurité, la disponibilité, la conformité et l'évolution. BUILD et RUN sont deux contextes d'un **même système d'autonomie**, pas deux autorités ni deux constitutions.

La maintenance autonome continue est le cœur du produit : écart entre exigences et réel → obligation durable → planification et exécution par agents → vérification indépendante → clôture ou escalade. Le travail peut prendre la forme de WorkItems, mais une obligation constitutionnelle ne se confond pas avec un ticket, un essai ou un agent.

## Parcours complet du produit

Standard doit pouvoir être installé sur un dépôt presque vide, un dépôt mêlant des contrôles partiels ou une plateforme déjà dotée de CI, IAM, SRE, politiques et observabilité. La présence d'un outil n'est ni une preuve de sa couverture ni une raison de le remplacer. L'installation découvre les capacités existantes, les confronte à la loi et choisit pour chaque responsabilité une route vérifiable : réutiliser, envelopper, compléter, créer ou signaler une impossibilité. Les déclarations de l'agent sur ce qu'il a découvert ne qualifient pas elles-mêmes la réalité physique.

1. **Constituer.** Épingler la release, la genèse, FLOOR-0 et les floors, composer la loi client sans affaiblissement, établir les identités et les procédures de décision. Même en partant de zéro, BUILD n'obtient aucune exception souveraine. Le provisionnement initial des T a une provenance et un contrôle indépendants de l'agent.
2. **Découvrir et qualifier.** Inventorier code, environnements, fournisseurs, instruments et contrôles existants ; nommer les sujets, les méthodes, la couverture et les routes possibles. Tester réellement les frontières T nécessaires à ces routes. Une responsabilité non qualifiée reste visible et bloque uniquement les opérations qui en dépendent.
3. **Projeter la loi sur le réel.** Transformer les exigences effectives en observations demandées. L'absence de mesure, la couverture inconnue, l'instrument indisponible, le risque constaté et l'effet incertain sont des situations distinctes. Le noyau conserve les obligations qui découlent des faits admissibles ; l'autonomie transforme les écarts en travail sans inventer de permission.
4. **Travailler en BUILD ou RUN.** Les agents conçoivent, codent, investiguent, testent et préparent des propositions, à l'intérieur de capacités bornées. BUILD peut créer une application depuis presque rien ; RUN observe activement dépôt et production, reprend les dettes, répond aux incidents et assure la conformité continue. Les WorkItems, retries et workflows restent remplaçables ; les obligations et leurs échéances survivent à ces changements.
5. **Décider et effectuer.** Une proposition d'effet est attachée au sujet, à la destination, aux octets et aux préconditions exacts. T authentifie et qualifie les prémisses ; K juge au préfixe authentique et produit le delta exhaustif ; la vérification indépendante intervient quand requise. Après commit durable, T garde les credentials, réserve, recontrôle au départ et exécute seulement l'effet autorisé. Une panne ou une réponse ambiguë devient `UNKNOWN`, puis travail de réconciliation, jamais succès présumé.
6. **Vérifier et poursuivre.** Une observation qualifiée du résultat et de la propriété exigée peut clore l'obligation ; un reçu d'exécution seul ne suffit pas. Sinon Standard reprend, restaure une route, renouvelle la preuve, réconcilie ou escalade. La surface humaine montre ce qui est maintenu, ce qui échappe à la couverture et les décisions réellement attendues ; l'audit conserve la trace détaillée.

Ce parcours est un **contrat du produit**, pas la description du niveau atteint par la démonstration actuelle. Aucune boucle de démo ne permet de sauter la qualification des T ou de convertir une sortie d'agent en fait indépendant.

## Architecture en quatre niveaux

1. **Surface produit** : état de santé, couverture, autonomie, risques, obligations, escalades et décisions humaines. Les empreintes et protocoles restent accessibles pour l'audit, non comme UX principale.
2. **Autonomie non souveraine (U)** : agents, WorkItems, workflows BUILD/RUN, scanners, observabilité, diagnostics, planification, réconciliation opérationnelle et adaptateurs aux outils existants. U propose et agit uniquement sous autorisations ; U ne définit pas la loi.
3. **Noyau constitutionnel hybride (K)** : un jugement déterministe unique sur identité, autorité, loi, état, preuves, obligations et effets. Il évalue des contraintes typées, dérive les conséquences obligatoires et prononce un delta atomique. Pas de mapping métier codé en dur ni de deuxième autorité.
4. **Trusted External (T)** : capacités indispensables dans le monde réel : identité/clé, horloge, ancrage durable, qualification des preuves, indépendance des vérificateurs, protection des secrets et des effets, réconciliation et progression vérifiable. Les T font partie de la **TCB effective** bien qu'ils soient hors du noyau pur.

K et T forment une frontière de confiance cohérente ; U n'est jamais un substitut à cette frontière. Les entreprises peuvent réutiliser IAM, CI/CD, cloud, catalogues, scanners, monitoring, gestion d'incidents et plateformes existantes **si leurs contrats vérifiables sont suffisants** ; Standard évite leur remplacement systématique.

Les garanties physiques **naissent de l'association K + T** : K spécifie et juge ce qu'il faut garantir, T établit hors de portée de l'agent les prémisses et le contrôle des effets, et les deux sont confrontés par des essais réels. Une interface Python ou une déclaration signée d'un fournisseur ne suffit pas à démontrer l'isolation des clés, la durabilité d'une ancre ou l'indépendance de deux personnes. Les neuf contrats T décrivent les responsabilités nécessaires selon la route, et non neuf composants à installer systématiquement.

Les adaptateurs appartiennent à deux positions possibles, selon leur pouvoir réel. La traduction, l'inventaire et la préparation d'une requête restent dans U. Un composant qui atteste une observation utilisée par K, conserve un secret privilégié ou fait partir un effet participe à la frontière T et doit être qualifié comme tel, même s'il se nomme « adaptateur ». Un outil déjà présent dans l'entreprise est traité selon le même critère. Le noyau ne code aucune API de fournisseur et ne laisse aucun adaptateur décider `allowed`.

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

**Surface AI-native :** les agents reçoivent automatiquement, pour la tâche et le sujet courants, une lecture textuelle de la loi effective signée, de la dette, des sources de preuve et de la route T. Ils peuvent demander le détail pertinent à partir de cette entrée unique ; ils ne doivent pas parcourir des fichiers de documentation ni interpréter la sérialisation du journal. Les règles propres au client s'écrivent hors des floors dans un fichier déclaratif borné ; sa présence dans un dépôt n'en fait pas la loi active. Seule la genèse ou une activation gouvernée donne autorité à son contenu. Toute projection porte le digest et le préfixe de cette loi et refuse une discordance.

## Protocole de bout en bout

`proposer → authentifier / qualifier → juger → vérifier lorsque requis → committer atomiquement → réserver / contrôler l'effet → exécuter ou marquer UNKNOWN → réconcilier → auditer / maintenir les obligations`.

Le commit doit être lié au préfixe constitutionnel authentique. L'effet est lié à une destination et à des octets exacts ; un effet autorisé mais non parti peut être bloqué par une restriction plus récente. Les hypothèses d'indépendance et de disponibilité des Trusted External doivent être exposées, pas simplement présumées.

## Frontière de confiance et garanties

Les responsabilités sont réparties entre **K** (prononce les conséquences légales), **T** (rend fiables les prémisses et effets physiques), **U** (réalise le travail). Il ne suffit pas de signer une affirmation `allowed` pour établir une autorité ; K dérive les droits de la constitution et de l'état authentique. Il ne suffit pas non plus de conserver un journal pour rendre impossible sa restauration : l'ancrage doit être indépendant de son domaine de restauration.

## Documentation de référence

- **[IMPLEMENTATION_CONTRACTS.md](IMPLEMENTATION_CONTRACTS.md)** : contrats par composant, scénarios d'échec, frontières K/T/U, garanties G01–G16 et tests de réception.

Les objets canoniques sont : constitution, principal, ressource, capacité, preuve, obligation, transition et intention d'effet. Le jugement unique combine les relations typées, les contraintes bornées et les conséquences exactes ; aucune ontologie GitHub, CI, SRE ou fournisseur ne peut se substituer à ces primitives.

**Frontière K ↔ T :** K qualifie les prémisses selon la constitution et produit verdict/delta/grant, T atteste l'identité et les événements physiques et applique les effets exclusivement ; un contexte signé `allowed=true` ne remplace jamais une autorisation dérivée par K. Les neuf fonctions de confiance sont des contrats regroupables, pas neuf microservices.

**Séquence :** proposition → authentification et preuve qualifiée → jugement → vérification indépendante si requise → commit ancré → réservation → contrôle au départ → résultat confirmé ou `UNKNOWN` → réconciliation et audit.

## Critères de validation avant production

Une release ne devient exploitable que lorsque les invariants et les responsabilités K/T/U sont vérifiés, que les tests adversariaux et de concurrence passent, que les hypothèses physiques des T sont prouvées pour le déploiement réel, que la performance est bornée et que les limites de couverture sont explicitement visibles aux utilisateurs. **Aucune déclaration de production-ready n'est implicite dans cette spécification.**

**Règle de réalisation :** toute intégration doit se rattacher à une étape du parcours, à un propriétaire K/T/U, à un contrat de preuve et à un scénario d'échec. Une fonctionnalité de démonstration ne devient une capacité de Standard que lorsqu'elle fonctionne sous la loi effective, emprunte la frontière physique requise, conserve la dette et expose honnêtement sa couverture. Les contrats et les tests de réception sont dans [IMPLEMENTATION_CONTRACTS.md](IMPLEMENTATION_CONTRACTS.md).
