# STANDARD — Contrats d'implémentation par composant

**Statut : direction normative de réalisation, pas attestation de production.** Document autonome avec contrats, invariants et tests par composant. Vue produit : [STANDARD_ARCHITECTURE.md](STANDARD_ARCHITECTURE.md).

## Principes transversaux exécutables

- **Un seul souverain déterministe : K.** Le noyau juge la constitution, l'autorité, les preuves recevables, l'état, les obligations et l'autorisation exacte des effets. Ni l'agent ni un Trusted External n'émettent `allowed` à sa place.
- **T rend les prémisses et effets réels** : clés/identités physiques, temps attesté, préfixe durable, vérité instrumentée, vérification indépendante, garde des secrets/egress et readback. T appartient à la TCB effective.
- **U propose, observe et réalise le travail** : build, monitoring, retries, WorkItems, workflows et outils. U n'est jamais autorité et un rapport signé de U n'est pas une preuve indépendante suffisante.
- **Mêmes octets et mêmes préfixes → même jugement.** Refus explicite d'une entrée malformée, d'un delta incomplet, de provenance insuffisante ou d'une dépendance T indispensable indisponible.
- **Aucune ontologie métier dans K.** Les schémas des ressources, outils et dépôts vivent hors du noyau ; leurs liens constitutionnels utilisent les primitives typées génériques. Aucun mapping `GitHub/CI/SRE → branche privilégiée du moteur`.
- **Temps et responsabilité distincts :** temps d'énoncé, ancre attestée et temps courant de départ ne se remplacent pas. Une autorisation ou l'écoulement du temps ne garantit pas l'exécution ni la convergence.
- **Chaque garantie G01–G16 ci-dessous a un propriétaire K/T/U, un invariant et un scénario de refus.** Une garantie fonctionnellement allouée n'est pas déclarée physiquement prouvée.

## I. Composants K — noyau hybride

| Composant logique | Contrat d'entrée → sortie | Implémentation prescrite | Refus/test essentiel |
|---|---|---|---|
| **K01 Canonical Model** | version, statements, graphe typé, snapshot → formes canoniques bornées | Structures fermées pour les primitives constitutionnelles ; identités stables ; encoding unique, versionné, sans données métier privilégiées | Forme ambiguë, champ caché, float/non-canonique, digest identique pour sens différents |
| **K02 Identity Semantics** | identities, signatures validées T02, domain/genesis → sujets authentifiés | Liaison au domaine, déclaration, ressource, type, version et préfixe exacts ; distinguer identité logique et preuve de personne physique | Réutilisation de signature cross-domain, cross-epoch, cross-resource |
| **K03 Authority** | sujet, capacité, rôle, graphe délégation, restrictions, temporel T03 → ensemble de droits | Atténuation monotone, absence de privilège par défaut, révocation/gel immédiats au préfixe, widening gouverné par quorum distinct, témoins, délais et veto | Un acteur se donne une capacité ; deux clés contrôlées par le même humain ne satisfont pas un quorum physique |
| **K04 Constitution** | FLOOR-0, floors release, clauses client, changement signé → loi effective épinglée | Composition non-affaiblissante ; changements de racine/dégel/droits suivant la procédure ; bootstrap et recovery sans exception souveraine | Une clause client affaiblit une protection de release |
| **K05 State & Transition** | snapshot ancré, demande qualifiée, loi → décision et delta exhaustif | Fonction pure unique ; vérifier préconditions et effets obligatoires/interdits, sérialiser les conflits, rejeter toute mutation non déclarée | Deux writers divergent ; delta seulement « autorisé » mais incomplet |
| **K06 Evidence Eligibility** | claim + attestations T06 + requirement/sujet/méthode/coverage/time → qualification | Séparer signature et vérité ; vérifier sujet exact, méthode, fraîcheur, couverture, source, indépendance et invalidation ; ne jamais déduire `healthy` du silence | Mesure signée mais mensongère, périmètre non couvert, agent auto-attestant |
| **K07 Obligation Ledger Semantics** | exigences, observations qualifiées, état antérieur → open/carry/close/due | Une dette stable par exigence/sujet/épisode d'écart ; tentatives et WorkItems ne remettent pas l'échéance à zéro ; retrait de loi distinct de réparation ; clôture sur preuve admissible | Huit retries créent huit dates ; renommage du ticket masque l'écart |
| **K08 Effect Intent & Permission** | décision et état actuel → effet canonique exact conditionnel | Définir destination, payload, transformation, préconditions, auteur, fenêtre et réconciliation ; re-juger au départ en cas de restriction pertinente ; aucune exécution dans K | Même op mais args différents ; capacité révoquée avant départ |
| **K09 Escalation Rules** | dette, loi, temps qualifié, tentatives → escalade exigible/maintien | Déterminer la condition constitutionnelle d'escalade indépendamment d'un scheduler ; aucune tentative échouée ne ferme une dette | Deadline dépassée mais obligation faussement close |
| **K10 Constitutional Judgment** | K01–K09 + préfixe/inputs épinglés → `Decision` | **Un seul** chemin de décision sémantique ; appliquer contraintes, relations, conséquences et delta comme une unité ; trace rejouable | Divergence entre sous-moteurs, fallback `allowed=true`, changement de résultat selon ordre arbitraire |

Ces composants sont des **contrats logiques**, non dix modules ou services imposés. Certaines vérifications peuvent être regroupées dans un code court ; elles ne peuvent être supprimées. Toute optimisation incrémentale doit être prouvée équivalente au jugement complet.

## II. Composants T — dépendances de confiance effectives

| Contrat | Port exigé | Règle de mise en œuvre | Test de falsification |
|---|---|---|---|
| **T01 Root/Runtime Pin** | `verify_release(runtime, genesis, law) → attestation` | Installer et ancrer hors de l'agent ; interdire downgrade et nouvelle genèse discrète | Binaire substitué, genèse réinitialisée |
| **T02 Keys/Physical Identity** | `authenticate(statement, roles) → identity_claim` | Custody exclusive, qualité de liaison physique et indépendance des humains/témoins documentées | Même opérateur avec plusieurs clés de quorum |
| **T03 Time** | `attest_time(event, uncertainty) → time_claim` | Séparer temps déclaré, témoin historique et départ ; comportement sûr sur horloges contradictoires | Faux futur accordant des droits |
| **T04 Durable Prefix** | `commit(expected_head, delta) → anchored_head` | Journal append-only, CAS atomique, ancre extérieure à la restauration, reprise avec vérification du préfixe | Rollback journal + pin local ; crash entre pin et commit |
| **T05 Independent Check** | `check(inputs, decision, delta) → agreement` | Implémentation et domaine de panne indépendants sur propriétés critiques ; bloquer désaccord | Même bug ou même input compromis accepté par deux copies identiques |
| **T06 Evidence Instruments** | `attest_measurement(subject, method, coverage) → observation` | Source et périmètre instrumentés, indépendants du bénéficiaire quand requis ; prouver ce qui a été réellement vu | Monde réel faux avec payload signé identique |
| **T07 Effect Guard** | `reserve_and_dispatch(effect, current_authority) → receipt` | Credentials/egress exclusifs, départ sérialisé, fencing, comparaison des octets exacts | Secret CI secondaire permet de déployer sans guard |
| **T08 Readback/Reconciliation** | `reconcile(reservation, provider_state) → evidence` | États `applied/not_applied/unknown` sans déduction abusive ; idempotence prouvée avant retry | ACK perdu après application, double action |
| **T09 Progress/Delivery** | `deliver_due(escalation, endpoint) → receipt` | Livraison et accusé observables sous conditions explicites de disponibilité/fairness ; aucune prétention de progrès absolu | Scheduler arrêté, silence interprété comme résolution |

**Déploiement :** ces neuf responsabilités ne prescrivent pas neuf services. Pour chacune, le déploiement déclare le fournisseur, le trust domain, la possession de clés, les droits de restauration, les chemins réseau, les dépendances communes, le protocole de panne et le test réel. Des services distincts sous un même administrateur ne sont pas une preuve d'indépendance.

## III. Composants U — autonomie BUILD/RUN

| Composant | Contrat | Interdiction |
|---|---|---|
| **U01 Discovery & Inventory** | Découvrir dépôts, assets, infrastructures et couverture ; produire des propositions d'observation | Ne peut déclarer une couverture complète sans instrument T06 suffisant |
| **U02 Requirement Projection** | Convertir floors + loi en objectifs observables, expliquer les écarts | Ne peut modifier la constitution pour simplifier une cible |
| **U03 Work Engine** | Créer, reprendre et réessayer les travaux pour satisfaire une obligation stable | Les WorkItems ne sont pas les obligations ; aucun reset de due |
| **U04 Agent Execution** | Planifier, coder, tester et proposer des changements sous capacités bornées | Aucun secret fournisseur privilégié ni signature souveraine |
| **U05 BUILD Pipeline** | Initialiser et transformer projets, produire artefacts et preuves | Pas de bootstrap constitutionnel god mode |
| **U06 RUN Pipeline** | Monitoring actif, incidents, corrections, maintenance continue, conformité | Un scan vert ne clôt pas automatiquement une dette |
| **U07 Integration Adapters** | Parler Git, CI, cloud, IAM, SRE ; exposer des modèles génériques | Un adaptateur ne peut autoriser une action ni fabriquer un fait qualifié |
| **U08 Human Surface** | Montrer couverture, objectifs, risques, dettes, décisions et escalades | Pas de traitement caché des risques non couverts comme « healthy » |

Le Work Engine peut absorber une complexité opérationnelle importante sans grossir la TCB. Les appels d'outils non sensibles n'ont pas besoin de jugement global à chaque étape : des capacités bornées, atténuantes et vérifiables suffisent lorsque le contrat l'autorise.

## IV. Répartition exhaustive des garanties G01–G16

| G | Obligation de K | Contrat T indispensable | Opérations U |
|---|---|---|---|
| G01 | Quorum, widening, veto, délais | Personnes/clefs/témoins distincts | Solliciter décisions |
| G02 | Restriction, priorité et re-jugement | Ordre atomique et fencing | Stopper les travaux |
| G03 | Floors, loi additive | Release pin authentique | Proposer règles |
| G04 | Delta canonique déterministe | Journal durable/ordre | Proposer modifications |
| G05 | Domaine/sens/signatures | Cryptographie, clés | Préparer assertions |
| G06 | Contraintes de temps ; jamais de droits par horloge | Temps et provenance | Retrys/backoff |
| G07 | Preuve recevable pour sujet/méthode/coverage | Vérité des instruments | Scanner |
| G08 | Ouverture, maintien, due, clôture | Rétention et observations fiables | WorkItems et réparations |
| G09 | Effet exact, re-jugement | Garde/egress exclusifs | Proposer effets |
| G10 | Réservation, état incertain, réconciliation | Fencing/readback/idempotence | Résoudre incertitudes |
| G11 | Refus d'état incompatible | Pins et domaines de restauration indépendants | Proposer recovery |
| G12 | Obligation de contrôle distinct | Vérificateur réellement indépendant | Diagnostics |
| G13 | Clôture par preuve seulement | Couverture et vérité mesurée | Inventaire et scans |
| G14 | Genèse/récupération gouvernées | Installer, racines physiques | Préparer initialisation |
| G15 | Définir tous les effets gouvernés | Fermeture des autres chemins privilégiés | Appels sous capacité |
| G16 | Permissions/dettes/conditions d'escalade | Livraison/disponibilité sous hypothèses | Scheduling et alertes |

**État de responsabilité : les seize garanties ont un découpage fonctionnel arrêté. État de preuve : leur démonstration en production reste indépendante et à établir.**

## V. Scénarios de réception obligatoires

1. **Widening adversarial :** une clé seule, plusieurs clés d'un même acteur, témoin non indépendant, mauvais délai, veto et dégel : aucun élargissement hors procédure.
2. **Law:** une loi client plus faible est refusée ; une loi plus stricte ne bloque pas abusivement les restrictions immédiates.
3. **Determinism:** entrée identique = delta identique ; delta incomplet ou additionnel = refus ; écritures concurrentes n'admettent qu'un préfixe linéarisé.
4. **Proof:** même payload signé pour deux réalités extérieures : pas de preuve de vérité sans source qualifiée ; mauvaise coverage ou sujet = refus.
5. **Obligation:** dette persistante sur huit cycles et plusieurs tentatives ; due conservé, clôture uniquement avec preuve indépendante et bonne coverage.
6. **Time:** l'agent antidate/surdater ; une horloge future ou contradictoire ne crée pas de droit.
7. **Effect:** différence d'octets, secret alternatif, révocation juste avant départ, ACK perdu et retry : blocage, UNKNOWN ou réconciliation prouvée.
8. **Rollback/Genesis:** écriture puis crash, restauration, pins déplacés, re-genèse : reprise ancrée ou arrêt.
9. **Checker:** fautes indépendantes injectées et désaccord bloquant, sans présumer qu'un second process est indépendant par défaut.
10. **Autonomy:** BUILD à partir de presque rien, RUN sur dépôt mature, outils existants intégrés sans donner d'autorité aux agents ; escalade due malgré interruption du scheduler.

Un scénario passant dans un simulateur ne prouve pas sa protection réelle ; préciser dans le rapport le **domaine observé**, la propriété affirmée, l'instrument de mesure et les hypothèses non vérifiées.

### Réception du parcours Standard entier

Les scénarios ci-dessus s'appliquent au [parcours complet](STANDARD_ARCHITECTURE.md#parcours-complet-du-produit), pas seulement à l'API du noyau. Une livraison intégrée doit permettre de suivre **un même sujet et une même obligation** à travers la constitution, la découverte, la mesure, le WorkItem, la proposition, l'effet, le readback et la nouvelle mesure. Les identités, préfixes, digests de loi et périmètres de preuve doivent rester liés à chaque passage.

| Porte | Résultat démontrable | Refus ou écart explicite |
|---|---|---|
| Constitution | Release et genèse épinglées ; loi client composée ; gouvernance active dès BUILD | Bootstrap local ou agent capable d'élargir son propre pouvoir |
| Réutilisation | Inventaire des outils existants, couverture, capacité et trust domain de chaque route | Présence d'un IAM, scanner ou CI interprétée comme garantie qualifiée |
| Obligation | Écart sous la loi effective, identité et échéance stables à travers BUILD/RUN et retries | Ticket fermé, cible renommée ou délai repoussé sans preuve |
| Travail | Work Engine et agents reprennent la dette ; route et capacités bornées ; egress gouverné | Modèle recevant un secret ou créant un commit par voie privilégiée parallèle |
| Frontière | Pour chaque opération, T requis qualifiés sur l'installation ; K juge une seule fois la sémantique constitutionnelle | Attestation statique, simulation ou signature de l'agent traitée comme fait physique |
| Effet | Réservation durable, contrôle exclusif, préconditions fournisseur exactes, reçu et réconciliation | GET puis PUT non atomique présenté comme CAS ; ACK perdu traité comme échec définitif |
| Résultat | Preuve de la propriété exigée au bon sujet et au bon horizon ; couverture et dette visibles | Reçu d'effet ou scan vert interprété seul comme clôture |
| Surface | Vue humaine BUILD/RUN des maintenances, trous de couverture et décisions à prendre | Rapport `IDLE` présenté comme certification ou fault masqué |

Une route sans T physiquement qualifié demeure inactive pour les opérations qui en dépendent ; elle peut néanmoins produire du travail de qualification et permettre les restrictions immédiates dont les autres contrats sont disponibles. La qualification est attachée à une release, une genèse, une installation et une route, avec tests de falsification et dépendances communes documentés. Le catalogue T est une liste de responsabilités, non un inventaire automatiquement vérifié de services.

Les opérations de la loi effective portent `trusted`, liste additive des responsabilités T propres à leur effet. T07/T08 restent exigés pour toute opération ; `tighten.ops.<op>.trusted` permet au client d'ajouter des contrats à une opération de floor sans les retirer. La préparation BUILD demande elle aussi T07/T08 à sa route. Le port d'effet requalifie sous la loi courante juste avant le fournisseur ; un contrat manquant arrête le départ et laisse l'obligation visible. Les enveloppes U sont liées au besoin et à la ressource exacte avant l'admission K, qui demeure la seule décision constitutionnelle. La présence d'un port ou d'un assessment signé ne prouve pas à elle seule son confinement physique.

## VI. Définition de terminé, par incrément et par release

**Pour un composant :** contrat de types/version défini, invariant testable, schéma d'erreur fail-closed, contre-exemple négatif, preuve de non-contournement, métrique de ressources, propriétaire d'intégration, absence de raccourci `allow` ou chemin privilégié secondaire.

**Pour l'ensemble de K :** un unique jugement canonique complet ; loi/racines/autorité/évidence/obligation/effet gouvernés ; résultat et delta vérifiables ; aucune branche métier cachée.

**Pour T :** chaque contrat déployé, son indépendance et ses chemins physiques audités ; pas de T manquant simulé silencieusement ; test de reprise, révocation et effets concurrents.

**Pour Standard :** BUILD/RUN fonctionnels avec Work Engine non souverain, maintenance continue sur obligations, expérience lisible de couverture et décisions humaines, et rapport de qualification sécurité/performance fidèle aux preuves réellement obtenues.

## VII. Ordre d'exécution

1. Fermer le **modèle canonique et les ports typés K↔T** avant de multiplier les implémentations ; un seul moteur souverain.
2. Implémenter la **constitution et l'autorité** (y compris bootstrap/récupération), puis **evidence et obligations**, avec contrats de refus et tests.
3. Raccorder **journal ancré + second contrôle**, puis **garde d'effets + UNKNOWN/readback**, sans mettre le provider dans K.
4. Brancher le **système autonome BUILD/RUN**, les intégrations et une surface humaine centrée sur couverture/dettes/risques.
5. Confronter G01–G16 à des tests réels contradictoires ; qualifier les Trusted External par installation ; optimiser uniquement après équivalence prouvée.

Ce plan fixe une **direction d'implémentation** ; il ne transforme pas une décision de conception en résultat de test.

## VIII. Contrat exécutable du noyau hybride

L'implémentation constitutionnelle unique réside dans `hybrid_kernel`. `Kernel.decide(snapshot, signed_entry)` produit le record et le delta requis ; `Kernel.judgment` sérialise le même résultat avec les empreintes avant/après. `Kernel.commit` rejoue les octets signés et refuse toute divergence du résultat, tout delta incomplet et tout préfixe périmé. Seul le journal réalise le commit durable après contrôle indépendant et rétention du pin. Les imports de compatibilité référencent cette même implémentation.

La loi peut déclarer `resources` : types avec champs scalaires fermés, états, état initial et table de transitions. Chaque transition déclare ses états de départ, son état d'arrivée, ses contraintes et la liste exacte des champs à écrire. Les déclarations ne peuvent écrire ni racines, ni droits, ni constitution, ni preuves, ni obligations. L'enregistrement exige `register:<type>` ; une transition exige `transition:<type>:<operation>`, le digest exact de la ressource, une chaîne active, ses conditions, ses budgets et l'absence de gel. Toutes les dettes déclarées par la loi restent dérivées dans le même delta.

Le prédicat positif `related: [relation, gauche, droite]` interroge exclusivement les relations constitutionnelles `role`, `holds`, `parent`, `owns`, `type`, `state`. Les paramètres peuvent être liés à `$author`, `$resource`, `$under`. Ces relations proviennent de l'état authentifié ; elles ne remplacent jamais la vérification de la chaîne d'autorité. Chaque interrogation est bornée et directe, sans exécution de code ni recherche non bornée.

La loi peut déclarer `instruments` : méthode, couverture exacte, sources, niveau minimal et fraîcheur. Pour une propriété instrumentée, une `observation` simple est refusée ; une `measurement` doit correspondre au contrat, dater une mesure récente et lier un artefact. Une restriction `invalidate` par un humain habilité ou la source de la mesure retire immédiatement sa recevabilité. Une mesure qualifiée n'affirme pas que K a observé lui-même le monde physique : T06 reste responsable de sa vérité.

Une dette de cible conserve son ouverture et son échéance à travers les tentatives et les changements d'alias ; une nouvelle déclaration ne peut repousser une échéance déjà ouverte. Le retrait d'une exigence est exposé comme `REQUIREMENT_RETIRED_WITHOUT_REPAIR_PROOF` ; sa réintroduction retrouve la dette. L'expiration d'une preuve instrumentée utilise la plus courte fraîcheur applicable. `debt.py` est une projection déterministe de responsabilité, jamais un second chemin d'autorisation.

Le bootstrap épingle tous les modules constitutionnels et les composants de confiance importables. Le budget K compte les primitives communes, les floors, les schémas et la dette, même lorsqu'ils sont réutilisés. Journal, pins, garde et contrôles AND restent dans le décompte distinct de la TCB effective. Les tests ne peuvent attribuer une qualification physique aux Trusted Externals : le manifeste de release conserve leurs critères non vérifiés.
