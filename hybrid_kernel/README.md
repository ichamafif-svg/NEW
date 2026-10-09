# Standard — prototype de noyau hybride (branche isolée)

**Branche :** `prototype/hybrid-kernel-v1`. **Statut : prototype fonctionnel partiel, architecture visée production ; NON production-ready.**

Ce prototype **réutilise** les primitives éprouvées des versions précédentes (`tcb.canon`, `tcb.policy`, `tcb.crypto`) au lieu de recoder une pile de cryptographie ou d'inventer un DSL. Il ne modifie pas `tcb/`, `ops/` ni le laboratoire figé. L'ancienne implémentation n'est pas remplacée.

## Architecture choisie

Une seule opération de **jugement** combine :
1. **Modèle canonique** : loi/version épinglées, état, obligations et demandes sur des ressources génériques ;
2. **Contraintes bornées** : programme positif fini validé par `tcb.policy`, pas de callbacks de règles arbitraires ;
3. **Transitions exhaustives** : chaque changement déclare son ancienne et sa nouvelle valeur, résultat `Decision` immuable avec delta complet ;
4. **Obligations autonomes par identité canonique** : ouverture et `due` préservés sous répétition des tentatives ; clôture impossible par simple affirmation ;
5. **Port d'admission Trusted External** : `hybrid_kernel.trusted.judge_signed` vérifie DSSE, signature Ed25519/WebAuthn selon clé épinglée, domaine, genèse logique du contrat, digest de la requête, état et loi ; `hybrid_kernel.core.judge` est **une primitive interne non sûre à exposer** ;
6. **Effets** : le jugement émet une description d'autorisation mais ne contacte aucun fournisseur. L'application réelle doit impérativement passer par une frontière externe exclusive.

Il n'existe **aucune table `type métier → handler`**. Un nouvel objet métier est une ressource générique et les règles sont des données de constitution validées. Le modèle constitutionnel, lui, conserve des primitives closes.

## Contrat et fichiers

- `hybrid_kernel/core.py` — validation de loi, décision pure, dette canonique, delta complet, vérification de commit en mémoire ;
- `hybrid_kernel/trusted.py` — admission via enveloppe DSSE et clé externement épinglée ;
- `tests/test_hybrid_kernel.py` — cas adversariaux de base ;
- `.github/workflows/hybrid-kernel-prototype.yml` — tests dédiés sur la branche.

**Important** : `commit` n'est pas un journal durable atomique ni une API sécurisée contre la concurrence. Une décision en mémoire ne doit jamais être interprétée comme une permission physique de déploiement.

## Critères non négociables avant déploiement

- [ ] États et loi en structures vérifiables, limitations de taille et de temps, schéma versionné ; refuser les objets malformés et les ambiguïtés ;
- [ ] Autorité constitutionnelle intégrale : quorum, restrictions, délégations atténuantes, évolutions de la loi, veto, récupération et bootstrap sans god mode ;
- [ ] Admission et signatures arrimées à des identités physiques réellement indépendantes et à un code/runtime épinglé ; revue crypto contradictoire ;
- [ ] Vérification de la provenance, fraîcheur et **indépendance réelle** des observations ; clés de mesures distinctes de celles de l'agent ;
- [ ] Cycle complet des obligations : création, maintien, échéance, clôture par preuve qualifiée, escalade et migration/renommage sans reset ;
- [ ] Stockage durable et linéarisable, anti-rollback indépendant, reprise et compare-and-swap atomique ;
- [ ] Effets exacts physiquement contrôlés : egress fermé, secrets hors agents, fencing, réservation, readback, incertitude des retries et revocation au départ ;
- [ ] Second juge indépendant et trace de jugement reproductible ;
- [ ] Tests adversariaux G01–G16, fuzzing, essais de panne, concurrence, replay, race clock/commit, provider mocks et tests d'intégration réels ;
- [ ] Budget de performance et de ressources défini, reproduit et vérifié sur charges cibles ; suite CI **verte et vérifiée**.

**Ne jamais promouvoir le prototype en production sur la seule base des tests unitaires verts.** L'architecture fonctionnelle visée est solide, mais la frontière de confiance effective n'est pas encore complète.

## Progression de réalisation

1. Construire une constitution/autorité typée et un journal atomique durable autour du jugement ;
2. Ajouter preuve qualifiée, clôture, escalation et vérification indépendante ;
3. Brancher un garde physique exclusif des effets sous tests adversariaux ;
4. Soumettre aux gates de sûreté/performance, puis décider d'une promotion explicite.

Le découpage de responsabilité déjà figé dans `tcb_lab/FUNCTIONAL_BOUNDARY_FREEZE_DECISION.md` reste l'autorité normative.

## Incrément 2 — Admission transactionnelle locale

`hybrid_kernel/store.py` introduit `SQLiteAdmission` : genèse non réinitialisable par l'API, transactions `BEGIN IMMEDIATE`, lecture contrôlée, jugement d'une enveloppe DSSE vérifiée sur l'état le plus récent, commit atomique du checkpoint et de l'enregistrement d'admission, identifiant de demande unique et rejet des reçus périmés. Le lien au `state_head` et à la constitution évite de réutiliser un reçu après une autre transition. `tests/test_hybrid_kernel_store.py` teste genèse unique, réouverture, identité de dette après retry, replay, refus et altération locale du checkpoint.

**Limite de confiance primordiale :** cette durabilité SQLite locale **ne résiste pas** à un adversaire capable de restaurer la base entière avec son journal ou de modifier simultanément checkpoint et lignes. Pas d'ancrage externe indépendant, pas de vérification d'identité physique de l'auteur sous-jacent, pas de règle de quorum complète, pas de preuve qualifiée de clôture, pas de garde fournisseur exclusif. Le jugement `ACCEPT` sur un effet **n'est pas** une autorisation physique de dispatch. N'exposer que le chemin `SQLiteAdmission.admit` derrière une API à contrôle d'accès ; `judge` et `commit` sont des primitives internes et acceptent des entrées non authentifiées si appelées hors du contrôleur.

**Séparation utile :** le jugement reste sans I/O dans `core.py` ; l'infrastructure de confiance prend en charge la signature dans `trusted.py` et l'atomicité locale dans `store.py`. Les opérations métier et la maintenance restent hors du cœur. Un déploiement cloud doit remplacer / compléter SQLite par un stockage à linéarisation et ancrage anti-rollback, sans changer les verdicts déterministes.

## Architecture conceptuelle — référence de conception avant poursuite du code

Les trois documents de conception désormais prioritaires sont :

1. [KERNEL_CONCEPTUAL_MODEL.md](KERNEL_CONCEPTUAL_MODEL.md) — jugement hybride unique, objets génériques, relations, cycles de vie et invariants.
2. [TRUSTED_EXTERNAL_CONTRACTS.md](TRUSTED_EXTERNAL_CONTRACTS.md) — neuf **contrats de confiance**, pas neuf microservices, avec frontières, failles et conditions de réutilisation.
3. [KERNEL_EXECUTION_PROTOCOL.md](KERNEL_EXECUTION_PROTOCOL.md) — admission, preuve, décision, commit, contrôle d'effet, incertitude, réconciliation et audit.

**Ordre d'autorité :** le scope et le découpage fonctionnel figés dans `tcb_lab/` sont normatifs ; les trois documents représentent la conception candidate ; le prototype actuel est une implémentation partielle qui **doit converger** vers celle-ci sans faire passer ses simplifications (`allowed=true`, SQLite local, effet abstrait) pour des propriétés de production. Aucun nouveau module fonctionnel ne doit être adopté sans traçabilité vers le modèle et les contrats T correspondants.

## Production gap / plan de réutilisation

La [matrice de réemploi et d'écarts](PRODUCTION_GAP_AND_REUSE.md) confronte directement `tcb/`, `hybrid_kernel/` et les trois contrats conceptuels. Elle distingue ce qu'on **réutilise**, ce qu'on **adapte**, ce qui doit rester **Trusted External** et ce qui reste hors du noyau pour préserver le produit BUILD/RUN. **Premier bloqueur P0** : l'admission signée `allowed=true` n'est pas encore un jugement constitutionnel d'autorité ; elle doit être remplacée par le pouvoir réellement dérivé des floors, du quorum et des délégations dans K. Statut : analyse d'écart enregistrée, aucun déploiement de production autorisé.
