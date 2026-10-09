# Phase 3 — Arbre expérimental vivant : PROFONDEUR × COUVERTURE

**Version 3 (2026-10-09). Source de vérité du plan expérimental et de ses dépendances.** Le scope constitutionnel [SCOPE.md](SCOPE.md) est figé. Les résultats servent **seulement** à trouver les questions suivantes : ni choix d'abstraction, ni refactoring, ni modifications du noyau historique.

## 1. Principe : un arbre de connaissance, pas une liste de tests

Une feuille suit toujours : **question falsifiable → hypothèses concurrentes → observations avec run+oracle → état de compréhension → expérience discriminante → nouveaux enfants**. Un test vert ne ferme pas une branche. Un résultat `OBSERVED` signifie mesuré, **pas sûr**. Une variation du résultat historique est un *finding* même si le workflow est vert.

Chaque nœud porte les champs : `id`, `parent`, `Gxx`, `responsibility`, `frontier`, `assumptions`, `safety_oracle`, `progress_oracle`, `competing_hypotheses`, `experiment_id`, `commit`, `run`, `actual_depth`, `status`, `what_would_falsify`, `children`. **Niveau exécuté ≠ niveau envisagé.** Les nœuds sans expérience sont `NOT_RUN`. Les expériences sans observation restent `CODED_NOT_OBSERVED`.

## 2. COUVERTURE — huit familles, seize garanties

| Branche | Garanties croisées | Domaine et question dominante | Lacune actuelle |
|---|---|---|---|
| **A** | G01 G02 G05 G14 | Identité, quorum, délégation, révocation, clés | séparation réelle des personnes et détenteurs de clés |
| **L** | G03 G04 G14 | Loi, floors, transitions et changement constitutionnel | loi modifiée entre autorisation et effet |
| **T** | G04 G06 G11 | Horloges, journal, pins, rollback et recovery | panne coordonnée, temps attesté divergent |
| **P** | G07 G12 G13 | Provenance, sujet, méthode, couverture, indépendance | différence authentification / qualification / vérité |
| **O** | G08 G13 G16 | Dette, délais, retrait, réparation, escalade | persistance d'un même sujet à travers multiples cycles |
| **E** | G02 G09 G10 G15 | Token, réservation, départ, incertitude et retry | anti-double-dispatch isolé, hôte/fournisseur réel |
| **B** | G05 G11 G14 G15 | Bootstrap, secrets, code pin et egress privilégié | frontière physique, credential alternatif, multi-hôte |
| **R** | G02 G07 G08 G09 G13 G16 | Maintenance autonome BUILD/RUN, incidents | liveness sous échec répété et sans autorité souveraine |

Croiser chaque branche avec les **7 responsabilités**, **3 frontières**, **5 contrats transversaux**, modes BUILD/RUN/recovery et contrôles négatifs **et positifs**. Cette matrice **n'implique pas** que chaque cellule est effectivement couverte.

## 3. PROFONDEUR — D0 à D7 (attribuer sur preuves uniquement)

| Niveau | Preuve expérimentale attendue | Ce que le niveau ne prouve pas |
|---|---|---|
| D0 | énoncé précis, hypothèses et oracles indépendants safety/progrès | comportement exécuté |
| D1 | cas atomique et deux témoins contrôlés | composition |
| D2 | mécanismes combinés et ordre inversé | concurrence réelle |
| D3 | séquence longue **sur le même sujet**, dette/échéance/progrès suivis | crash, multi-hôte |
| D4 | interleavings déterministes à chaque frontière critique | durabilité sous panne |
| D5 | kill/crash/recovery/pin et résultat d'effet inconnus | séparation physique |
| D6 | autre hôte/processus/fournisseur/secret réel et chemins alternatifs | vérification indépendante |
| D7 | adversaire adaptatif, contre-modèle et vérificateur réellement distinct | perfection ou absence universelle de défaut |

Nos premières séries de 400 demandes concernent **des ressources distinctes** ; elles ne démontrent donc pas D3 sur les obligations d'une cible. Les huit reprises E2 refusaient à cause de `HIST.TIME` ; elles ne démontraient **pas** un anti-double-dispatch.

## 4. Trois arbres actifs et prioritaires — campagne III

### O/R — Retrait et continuité autonome

```text
O1 — Repair red → withdrawn → cible encore dégradée
├─ O1.H1 : nouvelle tentative légitime parce que gap persiste
│  ├─ contrôle : gap toujours présent → nouvelle tentative permise
│  └─ contrôle : gap disparu → pas de nouvelle tentative inutile
├─ O1.H2 : loop/churn anormal d'une cible inchangée
│  ├─ vérifier même SHA, sujet, cause et échéance
│  └─ répéter 2, 3, 5, 20 cycles sur même cible
├─ O1.H3 : variabilité d'exécution / temps / fixture
│  ├─ même SHA + mêmes inputs + mêmes horloges → répétition
│  └─ capture IDs individuels et ordre des transitions
└─ O1.H4 : continuité d'obligation et escalade
   ├─ retain opened/due si réparer échoue
   └─ blocage justifié vs blocage silencieux
```

**Observé (campagne II) :** 10/10 essais à 2 cycles ont deux sujets `withdrawn` + `measuring`, `live=true`. Certains témoins à 3 cycles divergent. **Nouveau test III :** `p3_iii_autonomy_subjects.py` (18 variations avec sujets/temps exacts), `NOT_RUN` jusqu'à validation CI. Voir [Midpoint II](findings/P3_MIDPOINT_II.md). Les anciens rouges sont un signal de divergence de règle historique, **pas une vulnérabilité du noyau démontrée**.

### E — Effet incertain et protection réellement exercée

```text
E1 — intent → token → reservation → send → ACK
├─ E1.H1 : clock invalide produit le refus
│  └─ III : second temps = dernier événement durable + 1
├─ E1.H2 : barrière reservation/fencing bloque réellement replay
│  ├─ second guard / même journal
│  ├─ second journal / même SQLite
│  └─ deux processus / deux hôtes → non testé
├─ E1.H3 : provider "failed" après application partielle
│  ├─ pas envoyé / envoyé sans ACK / appliqué partiellement
│  └─ exigence de preuve externe pour statut non-appliqué
└─ E1.H4 : reprise après crash, law/revoke entre deux effets
   ├─ pause avant/après pin, send, ACK
   └─ re-jugement et reconciliation avant nouvel effet
```

**Observé (campagne II) :** huit répétitions refusées par `HIST.TIME`, pas par une garde anti-replay identifiable. **Nouveau test III :** `p3_iii_effect_clock.py` (8 cas à temps post-commit monotone), résultats `NOT_RUN` jusqu'à validation CI. Aucune garantie multi-hôte déduite.

### P — Preuve signée et vérité extérieure

```text
P1 — déclaration signée sur le sujet X
├─ P1.H1 : sujet/identité/niveau/temps sont correctement qualifiés
│  └─ contrôles séparés bon/mauvais sujet, auteur, grade, clock
├─ P1.H2 : l'oracle ment mais signature valide
│  ├─ contenu signé identique, "vérité" change hors noyau
│  └─ contenu signé mensonger, méthode vérifiable par second oracle
├─ P1.H3 : couverture, fraîcheur et méthode mal attestées
│  ├─ bon SHA, couverture insuffisante → refus / dette ?
│  └─ fausse couverture attestée par source partagée ?
└─ P1.H4 : preuve utilisée comme permission de clôture
   ├─ effet ok ≠ vérité indépendante sur cible
   └─ restauration/replay d'une attestation ancienne
```

**Observé (campagne II) :** `CAP.HOLDER`, `PROV.SUBJECT`, `NIV.CERTIFY`, `HIST.AHEAD` refusent les mauvaises déclarations ; `false_exact` est admise car l'indicateur de vérité externe ne figure **pas** dans la signature. **Nouveau test III :** `p3_iii_proof_epistemic.py` (6 contrastes et contrôle inter-cas), `NOT_RUN` jusqu'à validation CI. Il ne démontre pas à lui seul la vérité de l'oracle.

## 5. Arbres complémentaires indispensables

- **A :** quorum, veto, override, rotation et reconstitution des identités, collusion par clés physiquement communes.
- **L :** floor non affaibli, lois client, activation simultanée à un effet préparé, reprise d'un mandat expiré.
- **T :** temps signé / réalité discordants, pin/journal en décalage, rollback, restauration, préfixes partiellement écrits.
- **B :** bootstrap sans god-mode, egress alternatifs, secrets, runtime non pinné, fournisseur et hôtes indépendants.
- **R (transversal) :** maintenance de repo sans SRE, mixte, mature ; scanner absent, CI flapping, obligation non masquée, escalade justifiée.

Les parents sont documentés dans [GUARANTEE_MATRIX.md](GUARANTEE_MATRIX.md), [ATTACK_CATALOG.md](ATTACK_CATALOG.md), [ATTACK_EXPANSION.md](ATTACK_EXPANSION.md) et [P3_EXIT_CRITERIA.md](P3_EXIT_CRITERIA.md). Chaque nouvelle campagne doit **attribuer une feuille à toutes les garanties pertinentes**, et conserver les hypothèses de confiance non testées.

## 6. Ordonnanceur de recherche (pas d'agent autonome de production)

1. Choisir la feuille avec **signal rouge, oracle ambigu ou frontière la moins couverte**.
2. Vérifier le verdict de la mesure elle-même (pipefail, JSON, horloge monotone, anti-oracle tautologique).
3. Exécuter témoin positif, négatif et cas différentiel (un seul facteur).
4. Ajouter un interleaving puis une panne ; conserver les variations qui expliquent la divergence.
5. Publier `OBSERVED` / `INCONCLUSIVE` / `VIOLATION_OBSERVED` avec CI, SHA, fixture, signataires, sujet et effet.
6. Mettre à jour nœud parent et enfants, matrice empirique, midpoint et **limites**. **Jamais conclure un choix de design à partir du résultat.**

## 7. Convention de statut et critère de profondeur

`NOT_RUN` ; `CODED_NOT_OBSERVED` ; `OBSERVED` (mesuré, pas garanti) ; `INCONCLUSIVE` (mesure non discriminante) ; `VIOLATION_OBSERVED` (contre-exemple d'une propriété exactement énoncée) ; `BLOCKED` (exige infrastructure physique). Ne jamais classer `OBSERVED` comme `PASS` sans oracle indépendant. Les runs, cas et interprétations sont consignés dans [findings/README.md](findings/README.md) et le [registre automatique](https://github.com/ichamafif-svg/NEW/issues/2).

**La phase 3 reste ouverte.** Aucune couverture intégrale ou sécurité formelle revendiquée.

## Campagne IV — dimension FRONTIÈRE (superposée à profondeur × couverture)

Chaque feuille de G01–G16 porte désormais une **triple allocation non exclusive** : `K` (verdict constitutionnel déterministe), `T` (mécanisme externe de confiance indispensable à l'application ou la vérité) et `U` (acteur remplaçable sans souveraineté). Le statut `LIMIT_ESTABLISHED_LOGICAL` exige un argument d'indiscernabilité ou de capacité absente, des hypothèses et un contre-exemple ; `EXTERNAL_CONTRACT_REQUIRED` ne vaut pas validation physique. Référence exhaustive : [TCB_BOUNDARY_MATRIX.md](TCB_BOUNDARY_MATRIX.md), [ESTABLISHED_LIMITS.md](ESTABLISHED_LIMITS.md), [SCOPE_FREEZE_REVIEW.md](SCOPE_FREEZE_REVIEW.md). **Le scope sémantique antérieurement figé n'est pas modifié.**

## IV-B — revue des frontières et critères de fermeture

La [revue IV-B](IVB_BOUNDARY_CLOSURE.md) classe séparément les frontières `CLOSED_CONDITIONAL`, `OPEN_CRITICAL` et `OPEN_SEMANTIC` pour **G01–G16**, avec les contre-exemples et dépendances physiques. Quatre nouvelles expériences signées (effet révoqué, retry inconnu, preuve bon/mauvais sujet) sont intégrées à la CI via `p3_ivb_boundary_pairs.py`. **La classification ne constitue pas une validation de sûreté ; aucun scope ou noyau n'a été modifié.**

## Campagne IV-C — conclusion de délimitation (pas une preuve physique)

[IVC_BOUNDARY_DECISIONS.md](IVC_BOUNDARY_DECISIONS.md) passe en revue les **12 frontières antérieurement ouvertes** : dix allocations K/T/U deviennent **conditionnelles** sur la base de leurs contrats d'information et d'application ; **G08** (continuité des obligations) et **G16** (progression autonome) restent sémantiquement ouvertes. Avec les quatre allocations déjà conditionnelles en IV-B, on obtient **14 délimitations conditionnelles / 2 ouvertes**, *et non 14 garanties vérifiées*. Les contrats externes restent non validés physiquement. `p3_ivc_scope_audit.py` vérifie seulement la cohérence documentaire dans la CI, sans se substituer aux expériences adversariales manquantes. Aucun changement du scope sémantique [SCOPE.md](SCOPE.md) ou du noyau.

## IV-D — enfants actifs O/G08 et R/G16

**O.G08.D3** : une même cible sur 20 cycles, avec fail persistant vs signal scanner guéri à l'étape 6 ; comparer nouvelles propositions, identités de dette, âge et clôture. **R.G16.D3** : dégradation persistante vs contrôle sain sur 20 cycles ; séparer activité, progression effective et escalade. Expériences dans [P3_G08_G16_CAMPAIGN.md](findings/P3_G08_G16_CAMPAIGN.md). Le niveau D3 **n'est revendiqué qu'au titre de la durée de l'observation opérationnelle**, pas pour le suivi de dette constitutionnelle qui demeure non établi. Éviter d'inférer une garantie G08 ou G16 à partir de l'état `OBSERVED`.

## G08/G16 — lecture des résultats réels (après Actions 37964069387)

Voir [l'interprétation complète](findings/P3_G08_G16_FIRST_INTERPRETATION.md). Dans les scénarios à écart persistant, deux propositions sont retirées puis **18 cycles / 20 sans sujet live** sont observés, sans modification de main. Les obligations constitutionnelles ne peuvent pas être déduites de la seule liste `state["obligations"]` vide : **G08 reste ouvert**. **G16 reste ouvert** en attente du contrôle des escalades et de la fairness. Le prétendu contrôle sain était **invalide** (le runner `none` n'enlevait pas `vulns=found:2`) et a été rectifié dans le harnais ; ne pas citer l'ancien résultat comme témoin sain. Aucune modification du noyau ou du scope.

## Décision de consolidation — 9 octobre 2026 (statut actuel du **découpage**)

La [décision canonique de frontière fonctionnelle](FUNCTIONAL_BOUNDARY_FREEZE_DECISION.md) attribue désormais **16/16 garanties G01–G16 à K (décisions du noyau), T (Trusted External) et U (autonomie remplaçable)** sous hypothèses explicites. **Statut : CONDITIONAL_BOUNDARY_FROZEN**, et **non** 16 garanties prouvées. Les anciennes mentions `14 conditionnelles / 2 ouvertes` ou `OPEN_SEMANTIC` pour G08/G16 décrivent **l'étape IV-C/IV-D historique** et sont supplantées **uniquement pour la délimitation fonctionnelle** ; elles restent utiles comme état des preuves à leur date. G08 : dette canonique indépendante des tentatives ; G16 : règles de permission, dette et exigibilité d'escalade dans K, scheduling/retries/notification dans U et préconditions fiables dans T. La campagne IV-I et les travaux d'implémentation ne bloquent **pas** la décision de découpage. Le scope sémantique `SCOPE.md` demeure intact ; l'assurance physique, l'audit de déploiement et les portes de sortie P3 restent **ouverts**. Ne pas relancer une boucle de recherche sur tout Standard sans contre-exemple démontrant une mauvaise attribution K/T/U.

## Campagne V — étude d'architecture interne (démarrage)

Le [protocole comparatif](ARCHITECTURE_CAMPAIGN_V.md) confronte A (transitions), B (contraintes) et C (composition hybride) sur un [corpus d'oracles provisoire](experiments/architecture_oracle_cases.json), contrôlé automatiquement dans la CI. **Aucun candidat n'est sélectionné ; aucun prototype d'architecture n'est déclaré validé.** Cette recherche commence après le freeze 16/16 K/T/U et ne touche ni au noyau historique ni au scope.
