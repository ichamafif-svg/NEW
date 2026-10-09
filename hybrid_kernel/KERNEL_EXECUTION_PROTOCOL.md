# KERNEL_EXECUTION_PROTOCOL — protocole normatif conceptuel

**Statut : design candidat v1, pas contrat d'API déjà implémenté.** Références : [modèle](KERNEL_CONCEPTUAL_MODEL.md), [trusted external](TRUSTED_EXTERNAL_CONTRACTS.md), [scope](../tcb_lab/SCOPE.md). Le protocole couvre une transition ordinaire et une opération à effet. Il ne confond pas acceptation logique et effet physique.

## 1. Propriétés de bout en bout

- **Admission atomique :** une transition du préfixe N vers N+1 n'existe qu'après jugement déterministe et commit durable linéarisable ; rien ne change spontanément.
- **Autorité :** toute entrée est authentifiée et jugée selon la constitution épinglée au préfixe, les restrictions récentes et une chaîne de capacités valide. Aucune attestation générique `allowed=true` n'est une preuve suffisante.
- **Preuve :** une assertion qualifiée porte source, sujet exact, méthode, couverture, fraîcheur, preuve d'indépendance requise. Une clôture d'obligation par affirmation est interdite.
- **Effet :** la décision ne produit qu'une autorisation exacte et bornée ; le guard revalide au départ, réserve durablement et interdit les chemins non gouvernés.
- **Défaillance :** toute incertitude après l'entrée fournisseur demeure `UNKNOWN` jusqu'à readback autorisé ; une absence d'ACK n'autorise pas un retry aveugle.
- **Autonomie :** les agents peuvent planifier/itérer avec des capacités accordées ; les mutations constitutionnelles ne sont jamais auto-approuvées.

## 2. Machine à états canonique (conceptuelle)

`PROPOSED → [REJECTED | PENDING_INPUT | JUDGED] → COMMITTED → [NO_EFFECT | EFFECT_RESERVED → DISPATCHED → (CONFIRMED | UNKNOWN → RECONCILED)]`.

Les états d'effet appartiennent à un enregistrement canonique corrélé à l'intention. `UNKNOWN` **n'est pas** synonyme de rejet ou non-application. Restriction et révocation peuvent empêcher un départ non entamé, mais ne « désappliquent » pas un effet déjà entré chez le fournisseur. Reconciliation et compensation sont des opérations distinctes autorisées par contrat.

## 3. Flux détaillé

| Phase | Responsable | Entrée | Sortie, précondition de poursuite |
|---|---|---|---|
| 0 — sélection d'instance | T01/T04 | code pin, release, genèse, ancre | runtime et préfixe authentiques ; sinon stop |
| 1 — proposition | U | objet de demande, patch / opération souhaitée | déclaration bornée ; aucun privilège créé |
| 2 — admission externe | T02/T03/T06 | signatures, identité physique, temps, attestations | reçus authentiques, liés à domaine, requête, état et loi |
| 3 — jugement | K | snapshot pin, demande, entrées qualifiées | verdict pur + delta **complet** + obligations + éventuel grant exact |
| 4 — vérification contradictoire | T05 quand exigé | décision, entrées, runtime indépendant | accord vérifiable ou blocage |
| 5 — commit | T04 + K | préfixe attendu, décision et delta | CAS/transaction durable, anti-rollback, nouvel état unique |
| 6 — création d'intention d'effet | K | état commis, ressources, payload/destination exacts | autorisation liée à la constitution et au préfixe ; pas encore de départ |
| 7 — réservation & départ | T03/T07/T08 + K | autorisation, restrictions actuelles, réservation | exclusivité, re-jugement, fencing et octets identiques ; sinon refuse |
| 8 — accusé / réconciliation | T08 + K | réception, readback, observation attestée | `CONFIRMED` / `UNKNOWN` / transition réconciliée |
| 9 — obligation et audit | K/T04/T09/U | preuves, due, résultats, états | ouverture/maintien/clôture gouvernée ; escalade délivrée sous contrat |

La phase 7 **n'appelle pas nécessairement K pour chaque action technique** : elle applique une capacité bornée et une politique d'effet sous une garde de confiance, avec re-jugement constitutionnel seulement lorsque requis par le contrat. Elle ne peut pas réutiliser un état périmé qui autoriserait un effet révoqué.

## 4. Déroulements particuliers

**A. Réparation échouée, reprise, obligation persistante.** Le scanner découvre un écart, l'obligation canonique `requirement + subject + generation` s'ouvre avec `opened/due`. Les WorkItems successifs sont U. Après retrait, échec ou retry : mêmes identité et échéance si l'écart demeure. Seule une preuve qualifiée et une transition gouvernée peuvent clore. Si l'escalade est exigible, K la constate ; l'acheminement relève de T09/U.

**B. Révocation concurrente avec déploiement.** Avant le départ, T07 compare la dernière autorité appliquée, sous sérialisation/fencing avec T04 ; un jugement antérieur ne suffit pas. Si la révocation a été commise avant le départ, l'effet doit être bloqué. Un fournisseur déjà entré crée une incertitude à réconcilier, et non un rollback imaginaire.

**C. Timeout fournisseur.** Une réservation existe avant entrée. Sur timeout ou ACK perdu : `UNKNOWN`, conservation durable de l'identité d'opération, pas de nouvelle opération sémantiquement identique sans readback ou contrat idempotent démontré.

**D. Restauration.** T01/T04 contrôlent release, ancre indépendante et préfixe ; incohérence ou rollback = verrouillage de l'admission et du départ. Aucun mode récupération ne peut réinitialiser la constitution avec un seul acteur.

**E. Changement de loi.** Une clause client plus restrictive peut s'ajouter sous procédure gouvernée ; aucune modification de floors hors release Standard. Le nouveau contrat est épinglé pour les jugements suivants et les autorisations non encore parties doivent satisfaire les restrictions pertinentes.

## 5. Interfaces conceptuelles versionnées

`CanonicalStatement` : `domain, subject, operation, resource, nonce/id, before_digest, body, signatures`.

`QualifiedEvidence` : `claim_digest, exact_subject, requirement, method, coverage, source, timestamp, qualification, verifier_digest`.

`Judgment` : `verdict, reason, law_digest, before_digest, required_delta, obligations, conditional_effect, trace_digest`.

`CommitReceipt` : `old_head, new_head, epoch, durable_anchor, independent_verification`.

`EffectGrant` : `intent_digest, destination, exact_payload_digest, authority_scope, expiry, state_head, restrictions_epoch, reservation_id`.

`ProviderResult` : `reservation_id, entered_provider, result, source, evidence_digest, observed_at`.

Ces champs sont des intentions de contrat ; le schéma canonique exact doit être choisi par version de protocole et vérifié contre le modèle, sans créer un DSL implicite.

## 6. Invariants de reprise et de sécurité

1. Si T01–T08 sont indisponibles sur un chemin critique : aucun effet nouveau n'est réputé autorisé.
2. Le commit ne précède jamais la décision authentifiée.
3. La relecture déterministe retrouve état, obligations et décision du même préfixe.
4. Une entrée signée pour une autre requête, constitution, domaine ou état est rejetée.
5. Aucun résultat de fournisseur « incertain » ne revient par défaut à `not_dispatched`.
6. Un observateur ou outil U ne peut signer à la place d'une racine T ni s'octroyer un pouvoir.
7. Aucun système de notifications en panne ne clôt l'obligation constitutionnelle.
8. Un journal qui n'est protégé que par lui-même n'assure pas le non-rollback.
9. Chaque dépendance T revendiquée fournit un contrat testable et un mode de défaillance documenté.

## 7. Delta avec le prototype existant et ordre de réalisation

L'actuel `core.judge` valide un `context.allowed` simplifié ; `trusted.judge_signed` atteste un contexte, **sans** juger à lui seul les pouvoirs constitutionnels ; `store.SQLiteAdmission` sérialise localement sans ancrage indépendant ; `Decision.authorization` ne contient pas un contrat d'effet suffisamment précis pour le départ physique. Le code **ne réalise donc pas encore** les phases 0–9 de façon sûre.

Ordre recommandé : (1) constitution/autorité complète, (2) preuves qualifiées et obligations, (3) CAS durable + ancre indépendante, (4) contrat d'effet exact + garde exclusive, (5) seconde vérification et tests de panne, (6) qualification de production par déploiement cible. Chaque étape doit fournir ses scénarios adversariaux ; un rapport vert ne prouve pas les hypothèses physiques.

**Critère de promotion :** matrice G01–G16 démontrée sous hypothèses écrites, contrats T vérifiés sur une installation réelle, tests adversariaux indépendants, performances acceptables et décision explicite de release. Une architecture conceptuellement achevée ne constitue pas une certification.
