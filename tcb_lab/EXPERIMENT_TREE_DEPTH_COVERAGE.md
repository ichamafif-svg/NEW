# Phase 3 — Arbre expérimental : PROFONDEUR × COUVERTURE

**Mandat strict : observation et nouvelles expériences, pas de refactoring, pas de choix d'abstraction, pas de changement du scope constitutionnel.** Le scope figé dans [SCOPE.md](SCOPE.md) sert de référentiel ; une lacune de connaissance engendre des *questions*, pas automatiquement un nouveau concept.

## 1. Structure de l'arbre

```text
P3 : comprendre ce que la TCB fait, doit garantir et suppose
├─ COUVERTURE — quels pouvoirs et frontières sont effectivement explorés ?
│  ├─ A. Identité / autorité              G01 G02 G05 G14
│  ├─ L. Loi / constitution              G03 G04 G14
│  ├─ T. État / temps / historique        G04 G06 G11
│  ├─ P. Preuves / indépendance          G07 G12 G13
│  ├─ O. Obligations / continuité        G08 G13 G16
│  ├─ E. Effets / fournisseurs           G02 G09 G10 G15
│  ├─ B. Bootstrap / privilèges          G05 G11 G14 G15
│  └─ R. Autonomie BUILD + RUN           G02 G07 G08 G09 G13 G16
└─ PROFONDEUR — à chaque feuille de couverture :
   D0 question exacte, oracle safety et oracle de progression, hypothèses
   D1 test atomique / contrefactuel (+ témoin positif et négatif)
   D2 composition de 2–3 responsabilités, deux ordres opposés
   D3 séquence longue avec obligations et progression suivies dans le temps
   D4 concurrence ordonnancée : point d'interruption avant/après chaque frontière
   D5 panne / redémarrage / reprise / partition / rollback / délais
   D6 frontière physique : autre processus, hôte, secret ou fournisseur
   D7 adversaire adaptatif, oracle indépendant et réplication contradictoire
```

Un arbre n'est **pas** profond parce qu'il contient 500 mutations atomiques. Une feuille D1 ne couvre ni D5 ni D6. Inversement un test d'effet physique ne remplace pas l'audit des décisions exactes.

## 2. Matrice de couverture, sous forme d'arbres falsifiables

| Branche | Garanties | Ce que l'on veut comprendre | Oracle safety (violation cherchée) | Oracle autonomie/progrès | Extensions à attaquer |
|---|---|---|---|---|---|
| **A** Autorité et identité | G01 G02 G05 G14 | Quorum, delegation, revoke, freeze, rotation, separation physique | un seul acteur ouvre des droits; révocation contournée | agent habilité poursuit après refus hors scope | multi-clés, collusion, rotation, ancienne racine, recovery |
| **L** Loi et changements | G03 G04 G14 | Floors, client law, compatibilité temporelle de contrats | ancienne loi permet un effet devenu interdit | nouvel intent valable aboutit après changement gouverné | proposition/activation entre token reservation et départ |
| **T** Temps et historique | G04 G06 G11 | Horloges, checkpoint, antirollback, prefix signé | temps accorde un droit ou préfixe divergent accepté | progrès après recovery légitime et nouvelle ancre | clock skew, witness silence, restore journal/pins |
| **P** Faits, preuves, indépendance | G07 G12 G13 | Sujet exact, méthode, couverture, fraîcheur, oracles | assertion fausse ou partielle autorise/ferme | preuve valide reste utilisable sans approbation superflue | signatures communes, false green, faux univers, oracle compromis |
| **O** Obligations et redevabilité | G08 G13 G16 | Gap, dette continue, expiry, retry, repair, escalation | dette effacée, délai déplacé, fermeture sur faux succès | tentative échouée suivie de nouvelle réparation gouvernée | 100 renommages, CI flapping, downtime, multiples agents |
| **E** Effets et fournisseurs | G02 G09 G10 G15 | Intent, token, reservation, egress, response, reconcile | double effet, mauvais endpoint, effet après restriction | effet unique possible lorsque toutes conditions vraies | timeout post-application, failover, concurrent guards, side channel |
| **B** Bootstrap / domaines physiques | G05 G11 G14 G15 | Runtime, code pin, key custody, privileged writer, backups | run ancien privilégié, faux rollback, autre credential | restauration intègre sans god mode | 2 hosts, split-brain, credential leak, pin rollback |
| **R** Autonomie globale BUILD/RUN | G02 G07 G08 G09 G13 G16 | Discover→gap→work→check→effect→verify→close | agent auto-valide ou agit hors loi | maintenance autonome continue sous contraintes | repo vide/mature, 2 agents, incident, scanner offline, policy conflicts |

## 3. Développer chaque feuille selon les mêmes questions

**D0 — Définir sans présumer.** Entrée et préfixe exacts ; capacités des attaquants, acteurs indépendants, ressources, effet attendu, point de confiance ; prédire explicitement *ce qui serait une violation* et *ce qui serait une impasse injustifiée*. Toujours noter si le problème exige une hypothèse externe.

**D1 — Contrastes minimaux.** Candidat légitime, candidat identique avec un paramètre hostile, contrôle négatif et positif. Vérifier le refus/admission et la non-mutation après décision refusée.

**D2 — Composition.** A puis B, B puis A. Exemples : token → revoke et revoke → token ; evidence → law change et law change → evidence ; freeze → retry et retry → freeze. Un refus conditionnel peut être attendu ; le consigner.

**D3 — Durée.** Répéter les transitions d'un même *sujet* sur de nombreuses tentatives, pas seulement 80 sujets indépendants. Examiner obligation.opened/due, clôtures qualifiées, WorkItems échoués, nouvelles preuves et éventuelles escalades ; capter le préfixe et la dernière preuve après chaque étape.

**D4 — Interleavings.** Injecter une pause avant/après : admission, pin, reservation, re-jugement, send, ACK, observation, reconciliation. Tester chaque permutation déterministe, sans déduire d'une race aléatoire un ordre prouvé.

**D5 — Failles et reprise.** Kill entre deux écritures, horloge incohérente, disque plein, pin durable mais journal en retard, fournisseur appliqué mais ACK absent, scanner offline, quorum temporairement indisponible. Déterminer si le système *refuse*, *attend*, *escalade* ou *perd l'obligation*.

**D6 — Physique.** Déplacer la deuxième instance sur un vrai autre hôte ou un autre domaine de panne. Vérifier les permissions d'egress et les chemins alternatifs : un test local SQLite et un faux fournisseur ne démontrent aucune exclusivité globale.

**D7 — Contradiction indépendante.** Un deuxième instrument, une assertion externe au noyau, un adversaire qui change de stratégie à partir des refus observés. Reproduction du contre-exemple minimal et tests de non-trivialité (mutation délibérément dangereuse détectée).

## 4. Sous-arbres prioritaires : déclencheur → embranchements

### O1 — Réparation retirée mais cible encore dégradée (red test historique)

```text
red test_rule6_red_tests_withdraw_and_free_the_target
├─ H1 : oracle / fixture inexact
│  ├─ reproduire le même état avec une entrée contrôlée
│  └─ varier uniquement le SHA ou l'identité du sujet
├─ H2 : retrait correct, nouvelle proposition incorrecte
│  ├─ 1 seul agent / 2 agents
│  ├─ même cible / cible sœur / nouveau commit
│  └─ ordre retrait→réobservation / réobservation→retrait
├─ H3 : erreur de continuité d'obligation
│  ├─ retrouver opened / due / subject avant et après retrait
│  ├─ répéter 20 retraits, puis 100, observer dette et délais
│  └─ introduire des preuves indépendantes contradictoires
└─ H4 : arrêt volontaire par law ou restriction
   ├─ contrôle positif avec permissions disponibles
   └─ contrôle négatif sous freeze / revoke / budget épuisé
```

**Succès empirique :** comprendre précisément l'assertion qui échoue, avec un cas minimal et des témoins positifs/négatifs ; *pas* « rendre le test vert ».

### E1 — Effet inconnu et retry automatique

```text
intent → token → réservation → envoi → ACK perdu
├─ fournisseur n'a jamais reçu
├─ fournisseur a appliqué entièrement
├─ fournisseur a appliqué partiellement
└─ fournisseur répond tardivement
   ├─ même guard, même journal
   ├─ autre guard, journal partagé
   ├─ autre hôte, journal/credentials dissociés
   └─ revoke/freeze/expiration pendant incertitude
```

À chaque feuille : *nombre exact d'egress*, état durable de la dette, décision de retry, contrôle de progrès légitime après réconciliation.

### P1 — Preuve signé correctement mais trompeuse

```text
preuve signée sur sujet X
├─ faux contenu (instrument compromis)
├─ vrai contenu mais sujet Y
├─ bon sujet, mauvais SHA / mauvaise méthode
├─ preuve partielle annoncée comme couverture complète
├─ preuve périmée acceptée comme fraîche
└─ plusieurs oracles partageant source/clé/runner
```

À chaque feuille : permission ouverte ? obligation fermée ? trace de la source ? changement de résultat avec oracle extérieur ?

### R1 — Maintenance autonome prolongée

```text
repo dégradé → obligation → agent propose réparation
├─ CI rouge après réparation
│  ├─ réessayer légalement
│  ├─ budget épuisé → attente / escalade
│  └─ fail continuel sans redémarrer l'échéance
├─ scanner indisponible → absence de preuve ≠ preuve d'absence
├─ conflit avec autre agent → retrait + nouvelle tentative
├─ contrôle sec/SRE existant → ne pas créer autorité concurrente
└─ effet ok mais contrôle encore dégradé → dette reste ouverte
```

À chaque feuille : **aucun accès hors loi**, mais aussi état de la réparation, prochaine action possible et raison vérifiable des blocages.

## 5. Registre expérimental (une ligne par feuille, pas par famille)

| Champ | Obligatoire |
|---|---|
| ID parent/enfant | Exemple `P3/O1/H3/D3/rename-20` |
| Garantie et frontière | Gxx + décision, temps, egress, obligation, etc. |
| Hypothèses concurrentes | Au moins deux explications, incluant un défaut de test quand plausible |
| Oracle safety | Condition observable de violation |
| Oracle progression | Condition observable de possibilité d'action légitime ou de blocage justifié |
| Variables | Une dimension modifiée et les facteurs maintenus constants |
| Plan reproductible | script, seed, pause/fault point, processus, commit |
| Évidence | run, logs, JSON, head/size, effet simulé/réel, sujets exacts |
| Statut | NOT_RUN / CONFIRMED / REFUTED_UNDER_ASSUMPTIONS / INCONCLUSIVE / BLOCKED |
| Question suivante | Quelle expérience différente départage le reste ? |

## 6. Critère de COUVERTURE : pas uniquement G01–G16

On mesure séparément les couvertures **responsabilités (7), frontières (3), contrats transversaux (5), modes BUILD/RUN/recovery, dépendances physiques, chemins positifs et négatifs**. Une garantie attachée à trois composants exige des épreuves à chaque frontière et *entre* les frontières. Revoir les dépendances non visibles dans les fichiers TCB (credentials, scanners, sources de temps, OS, fournisseurs).

## 7. Critère de PROFONDEUR : refus du comptage superficiel

Pour chaque branche, enregistrer le Dmax **observé**, non le Dmax des fichiers écrits. Le niveau D7 n'est pas automatiquement nécessaire pour une propriété sans frontière physique ; noter pourquoi. Priorité P0 à toute feuille capable d'autoriser un effet interdit, de déclarer une dette close sans preuve, de masquer un écart durable ou de bloquer une action légitime sans motif. Les expérimentations peuvent ouvrir de nouveaux enfants indéfiniment : pas de promesse d'exhaustivité absolue.

## 8. Tableau initial d'avancement (conservateur)

| Branche | Niveau local documenté | Niveau observé certifié | Prochaine profondeur prioritaire |
|---|---|---|---|
| A — Autorité et identité | D1–D2 selon expériences existantes | **à attribuer par cas** | D2 rotation/collusion |
| L — Loi et changements | D1–D2 selon expériences existantes | **à attribuer par cas** | D2–D4 changement au départ |
| T — Temps et historique | D1–D2 selon expériences existantes | **à attribuer par cas** | D4–D5 ancre/pin |
| P — Faits, preuves, indépendance | D1–D2 selon expériences existantes | **à attribuer par cas** | D3–D6 faux oracle |
| O — Obligations et redevabilité | D1–D2 selon expériences existantes | **à attribuer par cas** | D3 obligations réelles |
| E — Effets et fournisseurs | D1–D2 selon expériences existantes | **à attribuer par cas** | D4–D6 départ + panne |
| B — Bootstrap / domaines physiques | D1–D2 selon expériences existantes | **à attribuer par cas** | D5–D6 reprise physique |
| R — Autonomie globale BUILD/RUN | D1–D2 selon expériences existantes | **à attribuer par cas** | D3 même sujet BUILD/RUN |

### Discipline finale

Les expériences en réussite montrent uniquement que les attaques tentées sont bloquées **sous leurs hypothèses**. Les tests rouges déclenchent une exploration des hypothèses et de l'oracle. Aucune conclusion de phase 3 ne modifie le scope ni ne présélectionne une abstraction. L'arbre décrit **le travail empirique restant**, pas une implémentation à construire.
