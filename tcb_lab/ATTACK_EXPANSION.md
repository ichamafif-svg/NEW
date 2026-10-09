# Phase 3 — Extension systématique des attaques (80 hypothèses)

**Statut de chaque scénario : HYPOTHESIS / NOT_RUN.** Ces scénarios servent à construire des reproductions; ce document n'affirme aucune exploitation. Les numéros E01–E80 désignent ici la campagne étendue, indépendamment des P3-01 à P3-24 de la matrice initiale.

L'enjeu n'est pas seulement l'absence d'actions interdites : **Standard doit maintenir une autonomie réelle**. Pour chaque propriété, tester deux faces : *safety* (ne jamais exécuter hors loi) et *liveness sous hypothèses* (une action légitime peut progresser, sinon la raison devient une obligation/escalade visible). Aucun dogme d'abstraction ne doit orienter les résultats.

## I — Identité / autorité

| ID | Attaque / perturbation | Violation recherchée (oracle) | Garanties | État |
|---|---|---|---|---|
| E01 | signatures d'une même clé sous plusieurs identifiants | quorum artificiellement atteint | G01/G05 | NOT_RUN |
| E02 | clé retirée puis réutilisée après rotation | action tardive admise | G01/G05 | NOT_RUN |
| E03 | acteur supprimé conservant une délégation secondaire | effet encore autorisé | G01/G02 | NOT_RUN |
| E04 | délégation sans borne temporelle acceptable | permission qui ne s'éteint pas | G01 | NOT_RUN |
| E05 | ressource sœur couverte par un préfixe trop large | accès non prévu | G01 | NOT_RUN |
| E06 | double comptage de cosignatures | quorum dépassé sans acteurs distincts | G01 | NOT_RUN |
| E07 | compromission d'un témoin et d'un oracle par même opérateur | indépendance fictive | G01/G07 | NOT_RUN |
| E08 | révocation de capacité par descendant | chaîne conserve une branche active | G02 | NOT_RUN |
| E09 | refus unilatéral suivi de sa levée implicite | gel disparu sans procédure | G02 | NOT_RUN |
| E10 | ancien signataire approuvant une activation sous nouvelle racine | élargissement admis | G01/G03 | NOT_RUN |

## L — Lois / constitution

| ID | Attaque / perturbation | Violation recherchée (oracle) | Garanties | État |
|---|---|---|---|---|
| E11 | ajout de condition contradictoire et négation cachée | voie d'autorisation inattendue | G03 | NOT_RUN |
| E12 | changement de type d'une ressource existante | contrat précédent réutilisé | G03/G04 | NOT_RUN |
| E13 | nouveau type d'effet reproduisant un effet interdit | contournement de floor | G03/G09 | NOT_RUN |
| E14 | changement d'alias entre deux versions de loi | preuve affectée au mauvais sujet | G03/G07 | NOT_RUN |
| E15 | affaiblissement indirect d'une exigence par discharge alternative | obligation fermée à moindre niveau | G03/G08 | NOT_RUN |
| E16 | règle impossible à satisfaire pendant RUN | maintenance définitivement bloquée | G03/G16 | NOT_RUN |
| E17 | cycle de dépendances entre exigences | déblocage indu ou impasse permanente | G03/G08 | NOT_RUN |
| E18 | édition concurrente de loi et d'une permission | ancienne politique appliquée après activation | G03/G09 | NOT_RUN |
| E19 | migration de release avec droits implicites | nouvelle genèse ouvre un chemin god | G03/G14 | NOT_RUN |
| E20 | contrat fournisseur modifié sans changement de digest visible | ancien intent encore exécuté | G03/G09 | NOT_RUN |

## T — Temps / ordre / concurrence

| ID | Attaque / perturbation | Violation recherchée (oracle) | Garanties | État |
|---|---|---|---|---|
| E21 | timestamp valide à la signature mais périmé au départ | effet dispatché malgré TTL | G06/G09 | NOT_RUN |
| E22 | checkpoint signé avec heure incohérente entre témoins | ancre avance abusivement | G06 | NOT_RUN |
| E23 | deux élargissements concurrents sur des racines divergentes | état final non déterministe | G03/G04 | NOT_RUN |
| E24 | restriction pendant lock de dispatch | départ postérieur à la restriction reconnue | G02/G09 | NOT_RUN |
| E25 | reservation conservée au-delà de DISPATCH_MS | envoi tardif | G06/G10 | NOT_RUN |
| E26 | avancée de temps sans entrée | permission nouvelle par lapse | G06 | NOT_RUN |
| E27 | retour arrière de l'horloge de l'hôte | nouvelle fenêtre de dispatch fictive | G06/G09 | NOT_RUN |
| E28 | deux instances distinctes avec journaux divergents | double effet fournisseur | G09/G10 | NOT_RUN |
| E29 | concurrence de révocation et rotation de clé | acteur retiré encore autorisé | G02/G05 | NOT_RUN |
| E30 | ordre différent d'observations simultanées | résultat de condition variable | G04/G07 | NOT_RUN |

## P — Preuve / confiance factuelle

| ID | Attaque / perturbation | Violation recherchée (oracle) | Garanties | État |
|---|---|---|---|---|
| E31 | scanner indépendamment signé mais rapport mensonger | réparation dangereuse admise | G07/G13 | NOT_RUN |
| E32 | rapport sur SHA A présenté comme preuve du SHA B | mauvaise transition autorisée | G07 | NOT_RUN |
| E33 | couverture partielle présentée comme totale | obligation déclarée satisfaite | G07/G08 | NOT_RUN |
| E34 | tests verts avec code candidat contrôlant runner | auto-validation dissimulée | G07/G16 | NOT_RUN |
| E35 | méthode de mesure modifiée après production du rapport | sens de preuve non épinglé | G07 | NOT_RUN |
| E36 | preuve authentique mais expirée réemployée | condition d'effet admise | G06/G07 | NOT_RUN |
| E37 | deux sources partageant la même pipeline d'ingestion | fausse indépendance | G07 | NOT_RUN |
| E38 | preuve d'absence fondée sur silence du scanner | autorisation depuis fait manquant | G07 | NOT_RUN |
| E39 | rapport de conformité présenté comme preuve technique | décharge injustifiée | G07/G13 | NOT_RUN |
| E40 | preuve issue d'une exécution partielle du test runner | résultat green malgré tests absents | G07/G13 | NOT_RUN |

## O — Obligations / autonomie

| ID | Attaque / perturbation | Violation recherchée (oracle) | Garanties | État |
|---|---|---|---|---|
| E41 | deux WorkItems concurrents pour même obligation | double clôture contradictoire | G08/G16 | NOT_RUN |
| E42 | renommage continu de cible | deadline reportée indéfiniment | G08 | NOT_RUN |
| E43 | suppression puis réapparition d'une exigence | dette effacée sans preuve | G08 | NOT_RUN |
| E44 | lancement d'une réparation qui échoue | obligation faussement fermée | G08/G13 | NOT_RUN |
| E45 | effet appliqué avec cible encore vulnérable | succès déclaré sans convergence | G08/G16 | NOT_RUN |
| E46 | génération infinie de nouvelles tentatives | autonomie sans progrès ni escalade | G08/G16 | NOT_RUN |
| E47 | absence d'observations pendant jours | silence traité comme bonne santé | G08/G16 | NOT_RUN |
| E48 | source indisponible empêchant toute preuve | système boucle au lieu de signaler | G08/G16 | NOT_RUN |
| E49 | échéance escaladée sans accusé de réception | escalade déclarée livrée | G08 | NOT_RUN |
| E50 | conditions trop strictes sans voie de réparation | autonomie impossible sans justification | G08/G16 | NOT_RUN |

## E — Effets / fournisseurs

| ID | Attaque / perturbation | Violation recherchée (oracle) | Garanties | État |
|---|---|---|---|---|
| E51 | appel fournisseur appliqué puis timeout | retry non idempotent | G09/G10 | NOT_RUN |
| E52 | adaptateur réécrit arguments après re-jugement | opération différente appliquée | G09 | NOT_RUN |
| E53 | endpoint alternatif utilisant credentials de l'agent | contournement complet du guard | G09/G15 | NOT_RUN |
| E54 | mutation d'un champ de requête ignoré par digest | résultat différent des octets jugés | G09 | NOT_RUN |
| E55 | base Git modifiée juste avant PATCH | effet sur précondition périmée | G09/G10 | NOT_RUN |
| E56 | fournisseur retourne 200 mais n'a pas appliqué | preuve d'effet inventée | G10/G13 | NOT_RUN |
| E57 | fournisseur renvoie 409 après application partielle | réconciliation erronée | G10 | NOT_RUN |
| E58 | reservation reconstituée depuis un snapshot ancien | seconde exécution | G10/G11 | NOT_RUN |
| E59 | deux tokens concurrents sur même effet non idempotent | deux départs valides non souhaités | G09/G10 | NOT_RUN |
| E60 | réconciliation not_applied malgré effet tardif | retry pendant effet en vol | G10 | NOT_RUN |

## B — Bootstrap / stockage / déploiement

| ID | Attaque / perturbation | Violation recherchée (oracle) | Garanties | État |
|---|---|---|---|---|
| E61 | pin et journal restaurés ensemble sur ancien snapshot | rollback accepté | G11 | NOT_RUN |
| E62 | remplacement d'une dépendance hors manifeste | code privilégié différent exécuté | G14/G15 | NOT_RUN |
| E63 | import Python avant vérification du bootstrap | code hostile exécuté avant scellement | G14 | NOT_RUN |
| E64 | clé gardée en mémoire par job non privilégié | chemin d'exécution parallèle | G15 | NOT_RUN |
| E65 | agent possédant token d'écriture non nécessaire | mise à jour du dépôt hors loi | G15/G16 | NOT_RUN |
| E66 | manifest approuvé mais fournisseur détourné par DNS/proxy | envoi à mauvaise destination | G09/G14 | NOT_RUN |
| E67 | crash après pin avant écriture journal | recovery perd ou double l'entrée | G11 | NOT_RUN |
| E68 | crash après provider send avant résultat journalisé | effet rejoué sans réconciliation | G10/G11 | NOT_RUN |
| E69 | restauration sur machine différente avec ancien témoin | ancienne autorité réacceptée | G11/G14 | NOT_RUN |
| E70 | suppression de clé guard lors d'un incident | récupération crée une permission god | G01/G14 | NOT_RUN |

## A — Autonomie maintenue sous adversité

| ID | Attaque / perturbation | Violation recherchée (oracle) | Garanties | État |
|---|---|---|---|---|
| E71 | CI flapping et preuves alternant vert/rouge | boucle d'effets sans stabilisation | G08/G16 | NOT_RUN |
| E72 | agent malveillant propose un correctif hors scope | effect appliqué malgré frontière | G09/G16 | NOT_RUN |
| E73 | scanner tombe en panne alors qu'un gel urgent apparaît | gel tardif car dépend de disponibilité scan | G02/G16 | NOT_RUN |
| E74 | agent ne sait pas réparer un contrôle organisationnel | escalade absente, obligation oubliée | G08/G16 | NOT_RUN |
| E75 | ressource inconnue pendant découverte initiale | besoin jamais représenté comme obligation | G08/G16 | NOT_RUN |
| E76 | client possède CI/OPA/Datadog préexistants | double autorité créée par Standard | G03/G15 | NOT_RUN |
| E77 | deux autonomies de maintenance sur le même dépôt | livraison non sérialisée et blocages | G09/G16 | NOT_RUN |
| E78 | repair validé mais sans credentials de déploiement | succès affiché bien que non appliqué | G10/G16 | NOT_RUN |
| E79 | restrictions successives pendant incident | système n'offre aucune voie d'escalade sûre | G02/G16 | NOT_RUN |
| E80 | dégradation contrôlée du réseau/temps/pins | indisponibilité silencieuse plutôt que blocage explicite | G06/G11/G16 | NOT_RUN |

## Critères d'investigation

Une ligne ne passe à **CONFIRMED** qu'avec un scénario isolé ayant produit la violation dans un environnement documenté ; elle passe à **REFUTED_UNDER_ASSUMPTIONS** seulement si le test a été exécuté et son oracle a effectivement rejeté l'attaque. Les environnements CI, les mocks et un vrai service GitHub se distinguent dans le rapport. Préférer tests de propriétés, permutations d'ordre, pannes injectées et interleavings aux cas uniques.

**Limites assumées :** certaines lignes concernent des domaines physiques ou organisationnels (quorum humain réel, contrôle exclusif des secrets, fournisseur, sauvegardes) non prouvables par un test purement Python. Ne jamais transformer une hypothèse externe en garantie de noyau.
