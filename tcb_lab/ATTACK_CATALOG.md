# Phase 3 — Registre d'attaques TCB (v1)

**Référence testée visée :** `main@d6347dccec714c0193bbc43af5de7e96e3a9ad27`. **Ne pas confondre ce registre avec des vulnérabilités confirmées.**

## Critères de résultat

- **NOT_RUN** : test/réproduction préparé, aucune exécution observable.
- **CONFIRMED** : la propriété ciblée a été violée dans l'environnement décrit et la reproduction est conservée.
- **REFUTED_UNDER_ASSUMPTIONS** : l'attaque a été bloquée dans les limites précises de l'environnement testé.
- **INCONCLUSIVE** : échec de l'instrumentation, preuve ambiguë ou hypothèse non vérifiable.
- **BLOCKED** : impossible à exécuter sans une ressource/une condition explicite.

Ne jamais déduire d'un test négatif la sûreté universelle. Les résultats des doubles fournisseurs restent **simulés**.

## Attaques préparées et prioritaires

| ID | Garanties | Attaquant / hypothèse | Tentative et oracle de succès | Reproduction | État |
|---|---|---|---|---|---|
| P3-01 | G01 G02 | agent signé non humain | faire admettre un gel sans pouvoir restrictif ; oracle = verdict | `p3_signed_core.py` | NOT_RUN |
| P3-02 | G04 G05 | adversaire rejoue une entrée signée | rejouer la même entrée après avance du préfixe ; oracle = mutation ou admission | idem | NOT_RUN |
| P3-03 | G05 | adversaire modifie signature | faire accepter l'enveloppe modifiée ; oracle = admission | idem | NOT_RUN |
| P3-04 | G01 G06 | acteur sans quorum | activation par seul temps ou signature isolée ; oracle = grant actif | idem | NOT_RUN |
| P3-05 | G02 G06 | deux humains restrictifs | bloquer une restriction par collision temporelle ; oracle = deuxième refus | idem | NOT_RUN |
| P3-06 | G07 | agent et source de faits distincts | ouvrir lui-même une condition de permission ; oracle = intent admise | idem | NOT_RUN |
| P3-07 | G04 | entrée malformée | obtenir admission ou mutation latérale ; oracle = préfixe modifié | idem | NOT_RUN |
| P3-08 | G01 G03 | client modifie sa loi | baisser quorum des témoins ; oracle = loi chargée | idem | NOT_RUN |
| P3-09 | G05 | deux identités logiques, même humain réel | passer k humains avec contrôle physique unique ; oracle = quorum admis malgré même personne | nécessite attestation identité humaine | BLOCKED |
| P3-10 | G07 G13 | oracle indépendant signé mais mensonger | faire admettre une action fondée sur preuve non vraie ; oracle = sortie malgré fausse propriété | fixture oracle + qualification | NOT_RUN |
| P3-11 | G07 G13 | source ne mesure qu'une partie d'un univers | observation « complete » malgré manque de couverture ; oracle = obligation close | faux instrument indépendant | NOT_RUN |
| P3-12 | G07 | attestation valide mais périmée | admission après TTL sous deux temps discordants ; oracle = effet | horloge simulée | NOT_RUN |
| P3-13 | G08 | acteur renomme la cible | réinitialiser échéance d'une dette continue ; oracle = date due plus tard | validation/adversarial + nouveau test | NOT_RUN |
| P3-14 | G08 G13 | effet annoncé ok, cible non réparée | vérifier que le succès ne clôt pas sa dette de preuve ; oracle = obligation ouverte | `p3_effect_line.py` (sous-ensemble), santé cible à tester | NOT_RUN |
| P3-15 | G09 | autre credential GitHub | mise à jour de main sans guard ; oracle = effet hors journal | **test sur dépôt éphémère uniquement** | BLOCKED |
| P3-16 | G09 G10 | deux guards sur hôtes distincts | deux départs du même effet après une restriction ; oracle = 2 appels fournisseur | `p3_effect_line.py` **SQLite local seulement** ; multi-hôtes non testé | NOT_RUN |
| P3-17 | G10 | fournisseur timeout après application | retry d'effet non idempotent ; oracle = double effet | `p3_effect_line.py` (injection résultat inconnu) | NOT_RUN |
| P3-18 | G10 | crash après pin / avant journal | perte ou duplication au recovery ; oracle = divergence indétectée | validation historique + injection | NOT_RUN |
| P3-19 | G11 | adversaire contrôle journal et pin locaux | rollback coordonné ; oracle = état ancien accepté | deux domaines de stockage simulés | NOT_RUN |
| P3-20 | G12 | même bug dans deux interpréteurs | entrée dangereuse acceptée conjointement ; oracle = violation de l'invariant externe | comparateur avec oracle indépendant | NOT_RUN |
| P3-21 | G09 | adaptateur change destination | effet vers ressource différente de celle jugée ; oracle = egress non conforme | fake port + interception | NOT_RUN |
| P3-22 | G14 | bootstrap ou récupération | contourner les restrictions via code avant scellement ; oracle = mutation non gouvernée | environnement isolé | NOT_RUN |
| P3-23 | G15 G16 | job scan/agent non fiable | obtenir un credential permettant update main ; oracle = action hors garde | revue de permissions et dépôt éphémère | NOT_RUN |
| P3-24 | G03 G04 | loi évolutive | supprimer invariant avec migration de release ; oracle = droits élargis sans protocole | fixture genèse/release neuve | NOT_RUN |

## Ensembles de frontières (campagnes)

**C1 : décision pure** — P3-01 à 08, 12 et 20 : élargissement, canon, temps, indépendance, loi.

**C2 : preuve et redevabilité** — P3-10 à 14 : mensonge signé, univers incomplet, obligation stable.

**C3 : effets et défaillances** — P3-15 à 18 et 21 : départ, concurrence, double effet, attente inconnue et reprise.

**C4 : confiance d'hébergement** — P3-09, 19, 22–24 : quorum réel, indépendance des pins, bootstrap, fuite de credentials.

## Observations de lecture statique — PAS de vulnérabilités confirmées

1. **Verrou local ≠ fence global :** `tcb/ledger.py::effect_gate` utilise SQLite `BEGIN IMMEDIATE`. Le contrat de sérialisation inter-hôtes/fournisseur doit être établi pour G09/G10.
2. **L'authenticité ≠ vérité du scanner :** le kernel qualifie des affirmations signées, mais `reproduced=yes` dépend des instruments et recettes externes ; G07/G13 requièrent une preuve de méthode et de couverture.
3. **Signature ≠ acteur physique unique :** une clé peut être contrôlée par un même opérateur ; G01 dépend des procédures de délivrance et séparation des clés.
4. **Adapter GitHub ≠ preuve d'exclusivité :** le `PATCH` `force=false` vérifie le fast-forward, mais non à lui seul l'absence d'autre détenteur d'un credential d'écriture.
5. **Pin distinct path ≠ domaine de restauration indépendant :** le déploiement doit isoler l'autorité sur les deux stockages pour G11.
6. **Double vérification ≠ complète indépendance :** les deux juges reposent sur certaines déclarations partagées, donc G12 exige une matrice de modes de défaillance communs.

## Exécuter sans ressource externe

```bash
python3 tcb_lab/experiments/g1_decision_probes.py
python3 tcb_lab/experiments/p3_signed_core.py
python3 tcb_lab/experiments/p3_effect_line.py
```

Ces scripts ne lancent aucune action fournisseur. Les observations doivent être archivées avec SHA de code et environnement avant changement de statut. Les 18 constats historiques restent un corpus d'attaques complémentaire : ils n'ont pas encore été reclassifiés ici.
