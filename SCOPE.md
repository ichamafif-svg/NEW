# TCB vNext — contrat de périmètre figé (scope freeze 1)

## 0. Statut et principe

Ce document fige **les responsabilités et les frontières**, non l'architecture interne, le langage, les API, les structures de données ni un nombre de lignes. Son changement ultérieur exige une décision explicite et une justification vérifiable. Le travail de recherche d'abstraction attend la validation du critère de complétude ci-dessous.

L'ancienne version n'impose **aucune compatibilité** de genèse, journal, signatures, fichiers, API ou implémentation. Une adoption vNext requiert une sélection explicite du code, de la constitution et de la genèse ; toute importation d'historique demeure une provenance, pas une conversion automatique en preuve vNext.

**Non-régression de garanties :** établir une matrice de correspondance entre chaque garantie réellement démontrée de l'ancien cœur et celle de vNext, avec preuves et hypothèses. Aucun affaiblissement tacite n'est permis. Une promesse historiquement non prouvée reste une obligation de démonstration, pas une garantie acquise.

## 1. Trois périmètres, définis par les pouvoirs

### A. Noyau constitutionnel déterministe

Décide des transitions admissibles à partir d'entrées canoniques, d'un état et d'une constitution épinglés. Une entrée identique sur un même préfixe et sous les mêmes hypothèses temporelles donne le même verdict et le même delta. Il ne contacte ni modèle, ni fournisseur, ni réseau, ni horloge ambiante pour calculer sa décision ; les valeurs temporelles lui sont transmises sous forme d'entrées dont l'origine est contrôlée par la frontière de confiance.

Sept **responsabilités sémantiques** (pas nécessairement sept modules) :

1. **Identity** : identités logiques, clés et liaisons authentifiées ; distinction des personnes/détenteurs physiques attestée hors du calcul pur.
2. **Authority** : rôles, capacités, portée, délégation atténuante, quorum, veto, révocation, gel, élargissement gouverné et absence d'acteur souverain.
3. **Law** : FLOOR-0 et floors épinglés par release, loi client additionnelle ou plus restrictive, validation et évolution constitutionnelle par transition autorisée.
4. **State** : état canonique, préconditions, transition unique et delta exhaustif requis/interdit, historique déterministe et interdiction de mutation spontanée.
5. **Evidence** : qualification d'une affirmation pour une exigence, un sujet et une méthode exacts ; validité, fraîcheur, couverture, provenance, indépendance, invalidation et limites explicites.
6. **Obligation** : dette persistante liée à une exigence et un sujet, date d'ouverture/échéance stable pendant un écart continu, résolution par preuve qualifiée, retrait gouverné distinct de réparation ; l'obligation n'accorde aucun droit.
7. **Effect** : description fournisseur-indépendante de la destination, des données sortantes, de la transformation, des préconditions, de l'autorité, de la fenêtre de départ et des conditions de réconciliation ; aucun effet physique dans le calcul pur.

Le noyau connaît des identités, ressources, contrats, faits qualifiés, permissions, obligations, états et effets ; **pas** de PR, Git, scanner, CI, SBOM, SRE particulier, modèle IA ou WorkItem.

### B. Infrastructure et dépendances de confiance

Le périmètre de confiance comprend tous les composants dont une défaillance peut permettre une action interdite, effacer l'historique ou faire déclarer vraie une clôture qui ouvre des droits, **quelle que soit leur localisation dans le dépôt**. En particulier :

- canonicalisation et validation bornée, primitives cryptographiques, liaison des signatures au sens et à la genèse ;
- bootstrap, sélection externe du code et de la constitution, intégrité du runtime, chaîne d'installation et contrôle des secrets ;
- admission durable, journal append-only, prévention du rollback par épingles dans un domaine de restauration indépendant, reprise exacte ;
- vérification indépendante des propriétés critiques, matrice de couverture et arrêt sur désaccord ;
- temps d'énoncé, temps attesté et temps actuel d'évaluation distincts ; horloge de départ protégée, expiration qui n'élargit jamais les droits ;
- réservation durable et non réutilisable, contrôle à l'instant du départ, sérialisation/fencing selon déploiement, isolation des credentials, vérification des octets exacts envoyés ;
- adaptateurs privilégiés, propriétés atomiques offertes par les fournisseurs, reçus et réconciliation sous incertitude ;
- qualification des sources de preuve qui débloquent des actions, y compris les scanners et instruments situés hors de la TCB locale.

La sécurité dépend aussi des fournisseurs, de l'OS, de la cryptographie, des horloges, du stockage et des domaines de panne. **Une faible taille du code local ne prouve pas une faible TCB effective.**

### C. Système autonome non souverain

Agents IA, observation, recherches, planification, production de patches, WorkItems, scanners, recettes, CI, télémétrie, présentation, SRE, sécurité opérationnelle et dossiers réglementaires peuvent être remplaçables. Ils n'autorisent ni n'attestent de leur seule initiative une décision qui serait suffisante pour passer à un effet. Un composant externe devient une **dépendance de sûreté** dès que son résultat peut débloquer un effet ; une permission d'écriture privilégiée le place dans la frontière de confiance.

## 2. Contrats transversaux obligatoires

**Transition.** Chaque mutation canonique correspond à une entrée authentifiée ; préconditions, delta obligatoire, delta interdit, obligations et conséquences doivent être contrôlés exhaustivement par rapport au préfixe et à la loi applicables. Une mutation seulement « permise » ne suffit pas.

**Temps.** Séparer le temps d'énoncé historique, l'ancre attestée par témoins et le temps courant vérifié au départ. Le temps ne crée aucun droit, seules des transitions explicitement autorisées peuvent élargir une autorité. Un horodatage d'agent ne décide jamais de la fraîcheur d'une permission.

**Preuve.** Qualifier par la relation `qualifies(proof, requirement, exact_subject, method, coverage, provenance, evaluated_at)`. Une signature prouve l'attribution, pas la vérité ; un digest prouve un lien aux octets, pas le sens du rapport. Toute exclusion et perte de couverture restent visibles. Le résultat « effet appliqué » et « exigence satisfaite » sont deux assertions distinctes.

**Effet.** L'intention gouverne destination complète, paramètres, contenu sortant, préconditions, identités autorisées et reprise. Aucun agent ne détient un chemin alternatif pour réaliser l'effet gouverné. Avant départ : réservation durable, recontrôle de l'autorité actuelle et comparaison de l'effet exact. Après entrée fournisseur, tout résultat incertain reste à réconcilier ; ni timeout, ni absence d'observation, ni commentaire ne prouvent une non-application définitive.

**Obligation.** Une obligation décrit ce qui manque ; le WorkItem n'est qu'une tentative de travail. Échecs, nouveaux commits et relances ne reportent pas arbitrairement son échéance. Fermeture seulement par contrat et preuve qualifiée ; changement de loi et retrait sont des issues distinctes de « réparé ».

## 3. Garanties planchers à conserver ou renforcer

- Aucun acteur unique ne possède l'ensemble des pouvoirs d'élargissement et d'activation ; quorum humain, témoins et délais attestés.
- Restrictions habilitées (veto, révocation, gel, signalement) applicables sans attendre un quorum d'élargissement ; dégel et dépassement du veto explicitement gouvernés.
- FLOOR-0 et floors non affaiblissables par la loi client ; délégation seulement atténuante ; permissions positives et limitées ; pas de permission déduite de l'absence de fait.
- Historique signé, genèse choisie extérieurement, persistance et détection de rollback avant acquittement, reprise exacte et refus conservateur en panne.
- Comparaison indépendante sur les propriétés critiques explicitement couvertes ; les dépendances communes et failles hors couverture sont documentées ; aucun « un bug seul » universel sans démonstration.
- Contrôle exclusif des effets gouvernés : réservation unique, décision actuelle, destination exacte, séparation des credentials, pas de répétition d'un effet incertain sans justification solide.
- Preuve fraîche, attribuée, portant sur le bon sujet et le bon univers ; invalidation et indépendance explicites lorsque la preuve autorise ou ferme une obligation de sûreté.
- Les écarts restent visibles avec ouverture et échéance stables ; la redevabilité n'attribue aucun droit ; un signalement d'escalade ne prouve pas sa réception.
- BUILD, RUN, initialisation et récupération ne créent aucun mode « god » exempté de la constitution.

La disponibilité, la convergence automatique, la conformité réglementaire et l'absence universelle de faute ne sont **pas** garanties par simple conception. Les hypothèses et modes d'échec seront déclarés et testés.

## 4. Hors périmètre constitutionnel, mais non dispensé de contrôle

Le noyau n'interprète pas les objets métier : GitHub/GitLab, modèle IA, politique ISO, versions de dépendances, outils SAST, WorkItems et interfaces. Les contrats déclaratifs d'exigence, preuve et effet permettent de les raccorder. Un adaptateur ne peut ni redéfinir la sémantique des permissions, ni auto-certifier l'exactitude de ses propres résultats.

## 5. Conditions de fermeture de la phase « scope »

Le périmètre est **figé par cette décision**. Sa **complétude démontrée** reste une porte distincte. Elle nécessite :

1. Inventaire exhaustif des promesses et surfaces d'effet, y compris egress et actions de préparation, avec propriétés falsifiables.
2. Pour chaque garantie : décision responsable, modèle d'échec, composant d'application, preuve, hypothèses externes et méthode de vérification.
3. Traçage de toutes les voies physiques d'écriture et des credentials ; absence de contournement non gouverné démontrée sur le déploiement cible.
4. Scénarios pour genèse, évolution de loi, restrictions, preuve périmée, temps, concurrence, crashs à chaque frontière, effet inconnu, reprise, migration et multi-instance (ou interdiction explicite).
5. Matrice `ancien comportement démontré → contrat vNext → preuve vNext`, sans prétendre importer la validité d'anciens journaux.
6. Revue contradictoire confirmant qu'une nouvelle intégration métier ne nécessite pas d'étendre les primitives constitutionnelles.

Toute question non démontrée demeure marquée **OPEN**, sans suppression ou assouplissement silencieux du contrat.

## 6. Discipline de changement

Le scope et ses garanties planchers sont des décisions de recherche : les modifications nécessitent un motif, un exemple falsifiable, une analyse d'impact sur la confiance et une décision explicite. **Pas de baisse des garanties au nom de la simplicité.** Les choix de langage, de modules, de DSL ou de stockage restent ouverts jusqu'à l'étude des causes racines.
