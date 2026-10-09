# TCB V6 : garanties et frontières réelles

La TCB locale inclut tous les modules Python de `tcb/`, le bootstrap et les éventuels adaptateurs déployés.
Chaque ligne est comptée dans exactement un budget, selon la garantie qu'un défaut de ce code peut casser :

| Budget | Modules | Un défaut peut | Plafond |
|---|---|---|---|
| Sûreté | tout le reste, bootstrap, adaptateurs | laisser passer un effet, un élargissement ou une réécriture interdits | 2 942 (historique) |
| Restrictif seul | `invariants` | seulement arrêter le journal : il ne juge qu'après une admission du noyau, et son échec arrête | taille au découpage, cliquet |
| Visibilité | `accountability`, `health`, `worker`, `sandbox` | masquer ou inventer un écart dans la santé, jamais admettre ni envoyer | taille au découpage, cliquet |

Un module ne sort du budget de sûreté que tant que la structure qui le justifie tient : `tools/check_tcb.py` vérifie qui
peut l'importer, `tests/test_budget_classification.py` vérifie la jonction par ET. Déplacer du code entre budgets est une
décision de revue, consignée dans `tcb-budget.json`, jamais un moyen de passer le contrôle.

## Loi et identité des contrats

FLOOR-0 gouverne les transitions critiques. Les floors Standard appartiennent à la release épinglée ; la loi
client les compose sans les retirer ni les affaiblir. Une loi client est apportée par la genèse, puis remplacée par
une proposition signée, un délai attesté et une activation. Le veto unilatéral et son dépassement par k+1 humains
avec double délai sont conservés. La racine exige k >= 2 et au moins k+2 humains, ainsi que le quorum de témoins.
Les changements de code/floors exigent une nouvelle release explicitement approuvée ; leur migration dans un même
journal n'est pas implémentée.

Chaque proposition est liée à la racine ET à la loi sous lesquelles elle a été approuvée. Toute proposition
antérieure à un changement de loi est refusée. Une capacité épingle le nom et le contenu de ses conditions ; un
effet épingle le contrat de son opération. Modifier ces contrats exige de nouvelles capacités ou intentions.
Les instances OBL et leurs clôtures épinglent aussi la définition de leur déclaration ; une nouvelle règle ne
solde pas une ancienne obligation et ses clôtures ne donnent pas de droits sous un contrat différent.
La relecture historique utilise la loi à la position de chaque entrée. Une activation est traitée sous l'ancienne
loi pour les transitions de cette entrée, puis les nouvelles cibles deviennent visibles.

La validation complète des cibles intervient avant admission. Une preuve de santé est liée à la définition complète
de sa cible : ressource, propriété, source, propriétaire, seuils, couverture et route. La redéfinition invalide cette
preuve. Un écart qui reste ouvert garde son ouverture et ne voit pas son échéance reculer ; son propriétaire est
actualisé. Retirer une cible client est une décision de loi gouvernée, visible dans l'historique ; ce retrait ne
constitue pas une preuve de réparation. Les floors ne peuvent pas être retirés.

## Frontière physique

Le guard écrit d'abord une réservation signée, durable et épinglée. Une réservation déjà consommée ne peut pas
être reprise, y compris après un crash. Aucun enregistrement de départ non signé ne sert d'autorité.
Sous le verrou d'écriture, le noyau et le vérificateur distinct recontrôlent l'autorité, les restrictions,
les conditions et le profil humain. Ils produisent chacun l'effet exact ; un désaccord sur ses octets canoniques
provoque un arrêt persistant. L'appel d'envoi à l'adaptateur a lieu avant la libération du verrou.

Un adaptateur peut retourner immédiatement un résultat ou une fonction d'attente du résultat d'une demande déjà
envoyée. L'attente est appelée hors du verrou. Elle ne doit jamais déclencher un nouvel effet : ce contrat repose
sur l'adaptateur, qui est de confiance et fait partie du périmètre audité. Une exception après entrée dans
l'adaptateur, y compris pendant l'attente, est `unknown` et conserve la réconciliation.
Un appel synchrone bloqué ou un envoi bloqué retarde encore les écritures ; aucune interface Python générique ne
peut garantir une borne à du code fournisseur arbitraire. Un adaptateur doit borner son envoi et ses I/O.
Une restriction admise avant l'envoi bloque l'effet. Après l'envoi, elle ne rappelle pas la requête.

Les arguments sont typés, la ressource est dérivée et une clé fournisseur lie la genèse à la réservation.
Une tentative locale unique ne prouve pas un effet distant unique ; la déduplication distante exige un fournisseur
qui honore cette clé. Aucun adaptateur fournisseur réel n'est inclus.

## Contrôles et dépendances

| Garantie | Contrôles | Limites communes |
|---|---|---|
| Autorité de l'effet | Admission signée, capacité bornée, deux évaluateurs des conditions, recontrôle au départ | Parsing canonique, état réduit, runtime, cryptographie et installation communs |
| Quorum et profil | Signatures, approbations liées à la racine, second contrôle à partir des déclarations épinglées | Identités logiques ; l'enrôlement doit établir les personnes physiques distinctes |
| Octets exécutés | Deux effets comparés, puis port canonique et adaptateur typé | Adaptateur et fournisseur de confiance pour l'action physique |
| Historique conservé | Chaîne signée, genèse externe, épingle monotone avant chaque acquittement | Stockage durable ; journal et épingles doivent survivre indépendamment aux restaurations |
| Usage unique | Réservation signée, consommation de l'obligation et contrainte SQL UNIQUE | SQLite, hôte ; pas de transaction atomique avec le fournisseur |
| Loi choisie | Proposition et activation gouvernées, loi de chaque entrée, contrats épinglés | La composition et la validation de loi ont une seule implémentation |
| Écarts visibles | Cibles validées, preuves liées à leur contrat, échéances et travailleur isolé | Couverture déclarée, sources, appel effectif de l'auditeur, témoins et horloge externe |
| Code choisi | Genèse liée au manifeste, bootstrap avant import, bytecode ignoré | Bootstrap installé de confiance, sources protégées pendant leur chargement, bibliothèques et OS |

Le second vérificateur prend un instantané des déclarations de la loi, pas des champs compilés mutables du noyau.
Il ne recopie pas cette loi à chaque entrée. Il réévalue séparément les cinq prédicats d'autorité des effets et
les transitions critiques couvertes par les probes. Il ne réévalue pas toute la loi : budgets de capacités,
composition, validation et conditions `when` des OBL restent notamment des dépendances communes ou sans seconde
implémentation exhaustive. F0-2 ne prouve donc pas qu'un composant quelconque peut être compromis sans conséquence.
Un désaccord de sûreté provoque un arrêt local persistant ; cet arrêt n'est pas une mutation canonique non signée.

## Redevabilité et vivacité

L'auditeur est injecté et ne peut écrire ni autoriser. Il maintient un travailleur confiné qui rejoue les entrées
signées par trames, puis seulement les ajouts. Une entrée reste limitée à 1 Mio, une trame à 2 Mio, une réponse à
8 Mio. La taille totale du journal n'est pas celle d'un paquet ; la reconstruction et la mémoire restent liées
à l'historique. Une panne, une limite ou une réponse incohérente donne `FAULT`.

Par défaut, une épingle qui avance pendant l'audit empêche de présenter l'ancien verdict comme actuel.
`health(prefix=True)` autorise explicitement un verdict pour son préfixe, avec `current: false` s'il est dépassé.
Chaque verdict nomme sa tête, sa taille, son temps signé et son horizon d'évaluation. Une horloge externe passée
par `required_at` révèle l'expiration des preuves même si les témoins restent silencieux, sans créer de droit.
Les états normaux sont PROVEN, IN_PROGRESS et ESCALATED ; FAULT reste un quatrième résultat d'exécution observable.

Une route de réparation est seulement une possibilité structurelle typée. Elle ne démontre ni la présence d'un
agent capable, ni ses permissions, ni un adaptateur implémenté, ni la réussite de la réparation. Une signature ne
prouve pas la vérité d'une source. Une escalade enregistrée ne prouve ni notification ni réponse humaine.
Il n'y a pas de preuve formelle de convergence, de certification réglementaire ou de consensus multi-hôte.
