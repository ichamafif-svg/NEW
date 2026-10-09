# Décision de recherche — frontière fonctionnelle du noyau (G01–G16)

**9 octobre 2026 · Décision de découpage, pas certificat de sûreté.** Le [scope sémantique préexistant](SCOPE.md) (Identity, Authority, Law, State, Evidence, Obligation, Effect) **n'est pas modifié**. Nous fermons la question « à qui appartient chaque responsabilité ? » pour les **16 garanties**, et non la vérification de leurs implémentations. Aucune architecture interne, algèbre, DSL, CIR ni topologie de déploiement n'est choisie ici.

## Règle de découpage

- **K — noyau déterministe** : prononce les transitions et responsabilités constitutionnelles, notamment légalité, pouvoir, preuve recevable, persistance/clôture des obligations et autorisation exacte des effets. Il ne réalise pas les opérations.
- **T — Trusted External** : fait tenir dans le monde réel les présupposés indispensables à ces décisions (identité physique, clés, horloge, ordre durable, indépendance de la preuve, garde des credentials, egress, readback, ancrage). **T reste dans la TCB effective**, même s'il est hors du code du noyau.
- **U — autonome non souverain** : planifie, mesure, crée des WorkItems, répare, teste, orchestre retries/backoffs, surveille et achemine les escalades dans des capacités bornées. Ses rapports ne deviennent pas vrais ni souverains parce qu'ils sont signés.

La fermeture d'une allocation est **CONDITIONAL_BOUNDARY_FROZEN** : elle signifie « K/T/U délimités avec contrats, hypothèses et falsificateurs ». Elle **ne signifie jamais** garantie démontrée, écosystème réellement isolé ou porte P3 satisfaite. Un défaut des contrats T bloque la mise en production même avec un K correct.

## Décision exhaustive par garantie

| Garantie | K : décision non délégable | T : dépendance de confiance | U : fonctionnement délégué |
|---|---|---|---|
| G01 | Signatures habilitées, quorum, délais, veto | Humains distincts, garde de clés et témoins indépendants | Sollicitations et coordination |
| G02 | Restriction/re-jugement dans l'ordre constitutionnel | Ordonnancement atomique de départ et fencing des effets | Gestion des travaux et alertes |
| G03 | Floors inaffaiblissables et loi client additive | Authenticité release/runtime/code pin | Rédaction de politiques plus strictes |
| G04 | Transition canonique déterministe | Transport/journal durable, ordre d'écriture | Propositions de transitions |
| G05 | Domaine, contenu, identité logique des signatures | Cryptographie, clés et identité physique | Préparation des demandes |
| G06 | Vérifier contrainte temporelle ; le temps ne crée pas de droits | Temps fiable et provenance attestée | Programmation et backoff |
| G07 | Recevabilité de preuve (sujet, source, méthode, fraîcheur, couverture) | Mesure véritable et indépendance réelle | Scans et collecte |
| G08 | Obligation canonique : ouverture, continuité, échéance, preuve de clôture | Rétention et ancrage durable ; observation couvrante | WorkItems, propositions, corrections, retries |
| G09 | Intention et effet exact autorisés puis re-jugés | Garde exclusive, politique d'effets, contrôle des octets | Plans et appels à capacités gouvernées |
| G10 | Réservation, incertitude et conditions de réconciliation | Fencing, idempotence, readback indépendant | Workflow de résolution |
| G11 | Rejet d'un préfixe/état incompatible avec son ancre | Pins indépendants et restauration fiable | Proposer recovery |
| G12 | Exiger un jugement distinct selon le contrat | Vérificateur réellement indépendant | Diagnostics non souverains |
| G13 | Seule une preuve qualifiée ferme une obligation | Vérité et complétude de la couverture mesurée | Inventaire et instrumentation |
| G14 | Genèse, évolution racine, récupération gouvernées | Installer/pin/identités/clefs racines fiables | Préparer création ou récupération |
| G15 | Définir les capacités d'effet admises | Fermeture de tous les chemins privilégiés alternatifs | Exécuter sous capacités bornées |
| G16 | Juger devoirs, permissions, échéances et conditions constitutionnelles d'escalade ; échec d'une tentative ≠ clôture | Livraison fiable des signaux exigés ; disponibilité/fairness externes sous hypothèses | Ordonnancement, réparations, backoff, monitor et notification |

## Conséquences particulières de IV-D à IV-H

**G08 :** [IV-H](findings/P3_G08_G16_IVH_CANONICAL.md) a observé l'objet `target:vulns` stable sur huit cycles malgré 1→4 propositions : `obligation`, `subject`, `opened`, `due`, `owner`. Cela rend crédible la séparation **obligation ≠ tentative**, sans démontrer le rollback, l'identité après renommage, ni une vérité externe. La frontière est figée **fonctionnellement**, pas attestée universellement.

**G16 :** [IV-E](findings/P3_G08_G16_PLAN_DIAGNOSTICS.md) a révélé des retraits et périodes sans action ; [IV-F](findings/P3_G08_G16_IVF_BACKOFF.md) une reprise après 25 heures ; [IV-G](findings/P3_G08_G16_IVG_HEALTH_ESCALATION.md) 21 lignes ouvertes sans escalade pendant la fenêtre ; **IV-I** franchit la date `due` pour audit du comportement. Rien de cela n'exige de placer un scheduler, les stratégies de retry ou un service de notification dans K. **La progression effective n'est garantie que sous hypothèses externes explicites de disponibilité, fairness et chemins permis.** K conserve l'obligation et évalue les conditions d'escalade prescrites par la loi ; le système extérieur la réalise.

## Stop-rule de recherche

Une expérience d'application **n'est plus une condition pour redéfinir K** tant qu'elle ne fournit pas un contre-exemple démontrant qu'une décision constitutionnelle indispensable a été laissée sans propriétaire K/T. Les enquêtes sur backoff, agent, WorkItem, ordonnanceur, scanner, provider ou alerting vont dans les **audits d'implémentation et d'intégration**, jamais en boucle comme condition de clôture de la frontière du noyau.

**Rouvrir la frontière seulement si :** propriété impossible à attribuer à K/T/U ; contournement de pouvoir imposant une nouvelle décision non couverte ; changement contradictoire du contrat constitutionnel ; falsificateur démontré non traitable par le contrat de confiance. Documenter la justification et un nouvel audit explicite, sans toucher automatiquement à SCOPE.md.

## Deux états distincts à maintenir

- **Découpage des garanties : 16/16 CONDITIONAL_BOUNDARY_FROZEN.**
- **Validation empirique/physique et passage P3 : OUVERTS ; aucune garantie globale déclarée prouvée.**

Références historiques : [IVB](IVB_BOUNDARY_CLOSURE.md) (4 conditionnelles / 12 ouvertes **au moment de IV-B**) et [IVC](IVC_BOUNDARY_DECISIONS.md) (14/2 **au moment de IV-C**). Ces nombres restent des **photographies datées**, désormais supplantées **pour le statut de découpage uniquement** par cette décision.
