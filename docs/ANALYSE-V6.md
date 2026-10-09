# Analyse de la fusion V6

## Conclusion et statut

V6 fusionne notre V0 et l'archive jointe `tcb-v5.zip`. Aucun contenu d'une V6 externe non fournie n'a été supposé.
La fusion conserve les protections de V0, reprend les lois en couches et la redevabilité injectée de V5, puis corrige
les changements de contrat et le départ physique. Le bilan exact des tests, du code et du budget est dans
`validation/summary.json`. Les scénarios adversariaux supplémentaires sont exécutables dans `tests/test_v6.py`.

Cette livraison reste un prototype à examiner. Le plafond historique de 2 942 lignes physiques n'est pas atteint
et n'a pas été relevé : le contrôle de budget échoue, même si les tests fonctionnels passent. Le résultat ne doit
pas être présenté comme une réduction achevée de la TCB, une preuve formelle ou une release acceptée par tous ses
critères. « Aucune régression observée dans ces scénarios » n'est pas « aucune régression possible ».

## 1. Ce que les deux bases apportent

| Sujet | V0 | V5 fournie | Choix V6 |
|---|---|---|---|
| Langage | Cinq prédicats positifs bornés | Conservé | Conservé, avec cohérence du champ `op` entre les deux juges |
| Gouvernance | Veto, k+1 pour dépassement, double délai, k+2 humains | Veto supprimé, k+1 humains | Protections V0 conservées, y compris pour un changement de loi |
| Loi client | Fixée par la genèse | Proposition et activation de loi | Évolution conservée, tous les objets affectés sont liés à leur contrat |
| Floors | FLOOR-0 | Floors Standard et composition client | Trois niveaux conservés ; un profil d'opération peut être renforcé |
| Redevabilité | Intégrée au journal pour l'orchestration | Injectée, imports vers l'intérieur | Injection conservée, validation des cibles déplacée avant admission |
| Départ fournisseur | Recontrôle et appel sous verrou | Départ logique sous verrou puis appel hors verrou | Envoi physique sous verrou ; seule une attente après envoi peut être différée |
| Audit concurrent | Audit dépassé refusé | Verdict d'un ancien préfixe accepté | Audit actuel par défaut, préfixe explicitement demandé et étiqueté |
| Taille locale | 2 894 lignes, plafond 2 942 | 3 154 lignes, plafond relevé à 3 200 | Comptage intégral conservé, dépassement visible et bloquant |

La fusion ne récupère pas un interpréteur ancien et ne simule pas une migration de journaux. Il faut une genèse
neuve et une sélection explicite du nouveau code. Cette décision correspond à une V0 sans clients de production.

## 2. Le vrai problème : l'identité des obligations, droits et preuves

Un nom reste insuffisant lorsque la loi devient mutable. Une entrée peut avoir été valide sous une loi, puis
être relue sous une autre ; une propriété peut conserver son identifiant tout en changeant de ressource ; une
opération peut garder son nom mais changer de profil. La sûreté exige de distinguer identité et définition.

| Objet | Ancrage V6 | Conséquence d'un changement |
|---|---|---|
| Proposition | Racine et loi au moment de l'approbation | Nouvelle proposition obligatoire |
| Capacité | Nom et contenu canonique des conditions | Une ancienne capacité ne reçoit pas la nouvelle interprétation |
| Intention | Contrat exact de l'opération | Nouvelle intention si arguments, ressource ou profil changent |
| Approbation humaine | Racine courante | Les anciennes approbations ne traversent pas une rotation |
| Preuve de santé | Définition complète de la cible | Redéfinition : preuve invalidée, observation nouvelle exigée |
| Obligation OBL | Contrat de sa déclaration | Une nouvelle règle de clôture ne solde pas une ancienne obligation |
| Clôture OBL | Contrat d'origine, provenance et fraîcheur | Elle n'accorde pas de droit sous une définition différente |

Cette règle remplace la réinterprétation implicite par des refus explicites. Une loi peut évoluer par gouvernance ;
les autorisations et les preuves ne suivent pas silencieusement cette évolution. Les identités de déclarations
versionnées sont préférables pour modifier une obligation qui a encore des instances ouvertes. Une instance
ancienne reste visible ; restaurer sa définition permet de la solder avec la preuve attendue. Les clôtures et
échéances ne sont pas réécrites comme si le nouveau contrat avait toujours existé.

Une cible client retirée par quorum devient une exigence retirée, pas une réparation prouvée. L'historique signé
conserve cette décision. Les floors Standard ne peuvent pas être retirés. Les cibles changées mais toujours
requises conservent les échéances des écarts ouverts : aucune succession de changements ne repousse leur dette.

## 3. Défauts reproduits et corrections

1. **Preuve pour une autre ressource.** Après une CI verte sur PR 42, le même ID de cible pouvait désigner PR 43 et
   rester PROVEN. V6 lie la preuve au contrat complet et demande une nouvelle observation.
2. **Ancien délai utilisé après changement de loi.** Une capacité proposée avec une heure de délai pouvait être
   activée après l'adoption d'un délai de deux heures. Toutes les propositions sont maintenant périmées au changement.
3. **Loi mal formée déjà activée.** Une fraîcheur nulle conduisait à FAULT seulement dans le travailleur. Le même
   validateur de cible intervient désormais avant admission ; les entrées mal formées sont refusées.
4. **Gel avant entrée fournisseur.** V5 relâchait le verrou avant l'appel. V6 conserve le verrou jusqu'à l'envoi réel.
5. **Effet du premier juge non comparé.** Dans les deux bases, le second juge vérifiait l'autorité de l'état mais pas
   le résultat exact renvoyé par le premier. V6 compare les deux effets canoniques avant le port.
6. **État compilé partagé.** V5 recopiait des champs compilés du noyau dans le vérificateur. V6 établit un instantané
   des déclarations épinglées et le réutilise pour cette loi, sans adopter les mutations du premier juge.
7. **Ancienne obligation soldée selon une nouvelle règle.** V6 lie instances et clôtures à leur déclaration.
8. **Activation comptabilisée sous la mauvaise loi.** Les transitions d'une activation sont traitées sous la loi
   qui l'a admise ; les nouvelles cibles s'appliquent ensuite.
9. **Route de réparation approximative.** Le contrôle ne se contente plus d'un motif textuel : il respecte types,
   valeurs répétées et limites des paramètres, avec une inversion déterministe du template.

Les tests simulent notamment un premier juge qui oublie une révocation, modifie le contenu de l'effet, élargit un
profil, active une proposition périmée ou falsifie le contrat d'une obligation. Le second contrôle bloque ces cas
et l'arrêt est conservé durablement. Les tests de rollback incluent révocation, gel et veto.

## 4. Juger, envoyer, attendre : la distinction nécessaire

Libérer un verrou avant l'appel ne supprime pas la fenêtre entre autorisation et action. Conserver un verrou
pendant toute la réponse bloque les restrictions lorsqu'un fournisseur prend longtemps. La séparation utile est
entre l'envoi et l'attente de sa réponse.

Le guard réserve durablement, rejuge sous le verrou et appelle l'adaptateur d'envoi sous ce même verrou. Ensuite,
un adaptateur correctement conçu peut fournir une fonction d'attente. Cette attente a lieu hors du verrou et ne
peut contractuellement lancer un autre effet. Une restriction peut donc être admise pendant l'attente ; elle ne
peut pas rappeler une demande qui a déjà quitté le système.

Ce n'est pas une transaction distribuée. L'adaptateur est de confiance, doit borner ses I/O et empêcher les
reprises implicites. Un adaptateur synchrone qui bloque retarde toujours les restrictions. Une exception après
entrée dans l'adaptateur reste UNKNOWN, même si elle porte le nom d'une erreur de validation. La réconciliation
reste ouverte et le même jeton ne peut pas être retenté. Il n'y a pas de fournisseur réel dans ce prototype.

## 5. Efficacité : ce qui est démontré et ce qui ne l'est pas

Le second vérificateur ne recopie plus la loi à chaque entrée : il prend un instantané lors d'un changement de
loi. La validation des cibles n'est pas recopiée dans deux composants ; elle est commune et s'exécute avant
admission. Le travailleur de santé reste persistant et incrémental. Les tests vérifient un journal de plus de
2 000 entrées, la reprise du travailleur, la cohérence avec une relecture complète et le coût d'écriture qui ne
croît pas avec la longueur du journal dans les cas mesurés.

Les microbenchmarks exploratoires enregistrés dans `validation/performance.json` ont mesuré :

| Mesure | V5 | V6 |
|---|---:|---:|
| Jugement + second contrôle, médiane, 2 000 répétitions | 0,324 ms | 0,291 ms |
| Écriture durable, médiane, 360 échantillons | 1,272 ms | 1,467 ms |

Le premier calcul est plus rapide dans cette mesure. Les écritures durables ont été plus lentes dans cet autre
échantillon, où SQLite, fsync et l'environnement jouent aussi un rôle. Il serait incorrect d'en déduire que V6
est plus rapide dans tous les cas ou qu'aucune régression de performance existe. Ces mesures sont exploratoires,
antérieures au dernier ajout de contrats OBL ; les résultats fonctionnels finaux portent sur le code livré.

La TCB totale n'a pas diminué. Déplacer la redevabilité dans un module injecté clarifie sa frontière, mais son code
compte encore pour la garantie de visibilité des écarts. Les bibliothèques et l'OS restent des dépendances externes
explicites. Aucun budget n'est respecté en supprimant les commentaires, en tassant le code ou en changeant le nom
d'un module de confiance.

## 6. Peut-on fragmenter davantage ?

Oui, par garantie et par pouvoir physique. Le noyau et l'intégrité définissent la base commune ; chaque port
fournisseur ajoute uniquement son envoi, ses préconditions et sa déduplication. La redevabilité n'autorise rien
et peut rester séparée. Les calculs de patchs restent hors de ces pouvoirs, avec un artefact et une révision cible
liés à une intention typée avant application.

Cette séparation donne des périmètres de revue plus petits. Elle ne réduit pas automatiquement leur union : les
contrôles de révocation, loi, genèse, réservation et preuve doivent rester cohérents entre ports. Une vraie
fragmentation multi-hôte exige encore un protocole d'ordre et de composition, absent ici. La V6 ne prétend pas
avoir démontré cette composition ; tous les effets physiques passent par la frontière commune du prototype.

Le prochain travail de réduction doit porter sur les mécanismes de représentation et de transition. Un budget
strict interdit de multiplier les compilateurs, variantes de langages et chemins de migration. Il ne justifie
pas de supprimer un mécanisme indépendant ou un contrôle physique pour faire baisser le chiffre.

## 7. Limite de « pas de régression »

Les tests sont des scénarios exécutés, pas une preuve universelle. Le second juge partage parsing, cryptographie,
runtime, état réduit et stockage ; il ne réimplémente pas toutes les règles, notamment la composition de loi et
les budgets de capacité. L'OS, l'installation du bootstrap, les clés, les personnes et les fournisseurs restent
des hypothèses. Les floors actuels sont un socle de démonstration, pas une implémentation de toute la conformité
ISO 27001, NIS2 ou DORA. Les notifications humaines, agents opérationnels et preuves de convergence sont absents.

L'acceptation complète de cette fusion reste donc bloquée par le budget. Le fichier permet d'examiner et de
rejouer le travail concret sans annoncer que tous les objectifs sont déjà satisfaits.
