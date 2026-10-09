# PRODUCTION_GAP_AND_REUSE — Alignement du noyau hybride avec Standard

**2026-10-09 — revue de code ciblée, sans revendication de certification.** Source normative : [scope figé](../tcb_lab/SCOPE.md), [16 allocations K/T/U](../tcb_lab/FUNCTIONAL_BOUNDARY_FREEZE_DECISION.md), [modèle conceptuel](KERNEL_CONCEPTUAL_MODEL.md), [contrats T](TRUSTED_EXTERNAL_CONTRACTS.md) et [protocole](KERNEL_EXECUTION_PROTOCOL.md).

## 1. Rappel du vrai produit

**Standard = plateforme AI-native de création et surtout de maintenance autonome continue des dépôts logiciels (BUILD/RUN), intégrant sécurité, SRE, conformité et infrastructures existantes, sans autorité souveraine d'agent.** Le noyau hybride n'est **ni** un ordonnanceur de WorkItems, **ni** un scanner, **ni** une plateforme de monitoring, **ni** un moteur de code. Sa finalité est de rendre gouvernables l'initiative et les effets des couches opérationnelles sans mapping métier figé. Toute extension du noyau doit correspondre à une propriété constitutionnelle, non à un cas d'usage SRE.

## 2. Inventaire des actifs disponibles et des décisions de reprise

| Source déjà présente | Propriété concrète observée dans le code | Destination | Choix | Condition avant promotion |
|---|---|---|---|---|
| `tcb/canon.py` | JSON canonique borné, parse rejette forme non canonique | K / codage des contrats | **REUSE** | Tests adversariaux profondeur/taille/types |
| `tcb/crypto.py` | DSSE/in-toto, Ed25519 et WebAuthn vérifiés | Port T02 / K domaine signé | **REUSE / WRAP** | Pin externe des clés, indépendance physique, anti-replay |
| `tcb/shapes.py` | Spécifications de formes, ressource / identifiants | K | **ADAPT** | Types fondationnels fermés, pas d'ontologie métier |
| `tcb/policy.py` | Langage fini positif, évaluation de faits vérifiés en amont | K, contraintes | **REUSE / EXTEND** | Exhaustivité des obligations, contraintes de floors/autorité |
| `tcb/obligations.py` | Déclarations ouvertes/fermées/gates ; délais et politiques de réouverture | K, obligations | **ADAPT** | Identité stable, migration, preuves de clôture, liveness conditionnelle |
| `tcb/kernel.py` | `decide(state, entry)` pur, séparation `apply` ; admissions HIST/SIG/TYPE/POLARITY/CAP/OBL | K, règles constitutionnelles | **EXTRACT / REFACTOR** | Éviter les kinds métier codés en dur, conserver les propriétés F0 démontrées |
| `tcb/floor0.py`, `tcb/floors.py`, `tcb/law.py` | Floors release, quorum/polarités, composition client + floors | K, constitution | **REUSE SEMANTICS / ADAPT** | Non-affaiblissement prouvé, versionnement, mutation gouvernée |
| `tcb/ledger.py`, `tcb/pins.py` | Journal SQLite, replay, checkpoints externes sous contrat | T04 | **ADAPT / WRAP** | Ancre vraiment indépendante, durabilité/fencing/restore |
| `tcb/invariants.py` | Second contrôle des changements critiques ; couverture partielle | T05 | **ADAPT** | Indépendance réelle de l'implémentation et du runtime, couverture exacte |
| `tcb/guard.py`, `tcb/effects.py` | Réservation, re-jugement, port d'effet à adaptateurs explicites | T07/T08 | **ADAPT / WRAP** | Contrôle egress exclusif, bytes exacts, readback, ACK inconnu |
| `tcb/accountability.py`, `tcb/targets.py`, `tcb/health.py` | Suivi déterministe de conformité sur journal, due et escalade logique | K/T09/U selon pouvoir | **SPLIT** | N'intégrer à K que dette/qualification/exigibilité ; laisser monitoring et orchestration dehors |
| `hybrid_kernel/core.py` | Modèle générique et delta déterministe partiel | K, prototype | **REWORK** | Admission constitutionnelle non réductible à `context.allowed` |
| `hybrid_kernel/trusted.py` | Signature DSSE du contexte, liée request/state/law | T02 | **WRAP** | Attestation ≠ autorisation ; vérifier la chaîne des droits dans K |
| `hybrid_kernel/store.py` | Transaction locale SQLite, unicité d'identifiant, cohérence état/ledger | T04 local | **ADAPT** | Empêcher rollback coordonné / concurrence / altération physique |

**Aucun statut REUSE ne signifie « sûr en production ».** Les modules hérités sont des matériaux de conception et des sources de tests, non des certificats.

## 3. Les vrais écarts constitutionnels (bloquants)

| Priorité | Écart actuel du prototype | Propriété attendue | Source de réemploi |
|---|---|---|---|
| P0 | Une attestation signée fournit `allowed=true` sans vérifier la constitution complète | Autorité, délégation atténuante, quorum/veto, restrictions, loi gouvernée évaluées **dans K** | kernel/floor0/law |
| P0 | `commit` et `SQLiteAdmission` n'ont pas d'ancrage indépendant du stockage | Journal non restaurable à un état antérieur en production | ledger/pins |
| P0 | Les autorisations d'effet n'incluent pas de revalidation physique exacte | Pas de départ hors effet autorisé et de chemin alternatif | guard/effects |
| P0 | Clôture d'obligation toujours en `PENDING_EXTERNAL` | Fermer seulement avec preuve qualifiée d'un vérificateur indépendant | obligations/accountability |
| P0 | Décision secondaire et couverture indépendante non intégrées | Pas de promotion sur le seul verdict d'un juge | invariants |
| P1 | Identité de dette simple `kind + subject` | Traitement explicite des changements de sujet, générations et lois | obligations/targets |
| P1 | Conditions d'escalade et preuve d'acheminement séparées non achevées | Jugement du dû par K, livraison sous contrat T09 | accountability |
| P1 | Définition d'une ressource générique mais primitives constitutionnelles incomplètes | Modèle extensible sans mapping rigide | shapes/policy/kernel |
| P1 | Absence de tests de continuité sur backend réel et panne | Tests adversariaux G01–G16, crash, concurrency, replay, failover | lab + tests existants |
| P2 | Aucune qualification de charges/performance et de schémas stable | Borne de ressources, mesures et compatibilité versionnée | scripts/CI |

## 4. Contrat de réalisation « production first »

La réalisation doit produire **un seul cœur constitutionnel**, non deux noyaux concurrents (`tcb/` et `hybrid_kernel/` en parallèle à long terme). Le noyau historique reste intact jusqu'à une **démonstration de non-régression explicite**, puis une migration/version de release et genèse nouvelle selon [SCOPE.md](../tcb_lab/SCOPE.md). Les Trusted External sont des ports contractuels ; leurs implémentations physiques sont qualifiées séparément.

**Ordre des incréments :**
1. **Autorité + loi** : remplacer `allowed=true` par la vérification constitutionnelle complète, réutiliser les obligations signées et la logique de quorum/veto/restriction. Ne pas casser le chemin de restriction immédiate.
2. **Obligation + preuve** : relier faits qualifiés, identité de dette, clôture, due/escalation sans importer le scheduler des WorkItems.
3. **Persistance + vérification indépendante** : extraire le contrat de journal, ancre indépendante, seconde décision.
4. **Effets et garanties physiques** : authorization exact, reservation, exclusivité de secret, re-jugement au départ, `UNKNOWN` + réconciliation.
5. **Cohérence BUILD/RUN et réemploi client** : ports standards pour adaptateurs et telemetry ; les workflows du produit restent U.
6. **Gates de promotion** : corpus G01–G16, divergences anciennes/nouvelles, scénarios réseau/OS/fournisseurs, test de panne, profiling et revue indépendante.

À chaque incrément : une interface stable, des exemples de vérité et de refus, des tests adversariaux, une preuve claire du fait que le chemin privilégié ne contourne pas K/T. Les métriques à suivre sont **complexité de preuve, hypothèses de confiance physiques, chemins d'effet, latence p95, risques de dégradation**, et non les seules lignes de code.

## 5. Décision de produit

Ne pas construire une usine à constitution en laissant de côté Standard : pas de CLI/SRE/CI scanner dans K, pas de nouveau mapping GitHub/Kubernetes, pas d'interface centrée sur les empreintes et le YAML. La surface humaine du produit doit afficher **ce qui est maintenu, non maintenu, pourquoi, quels écarts persistent, quels risques ne sont pas couverts et quelles décisions sont réellement requises**. Le système U réalise l'autonomie, K prend les décisions et T rend certaines garanties effectives.

## 6. État et honnêteté de la preuve

**STATUT : GAP_ANALYSIS_RECORDED — production readiness BLOCKED.** Inventaire fondé sur la lecture des fichiers et leurs entêtes/points d'entrée ; il ne vaut ni audit exhaustif ligne par ligne ni validation physique. L'implémentation actuelle reste partielle. Le prochain incrément doit être accompagné de tests exécutés, pas simplement écrits.
