# G1 — Hypothèses de menace et frontières à éprouver

**Date :** 2026-10-09. **Référence :** main@d6347dc. Recherche de portée uniquement, aucune abstraction adoptée.

## Acteurs et domaines de panne

- Agent capable de proposer des entrées, du code, des fichiers et des sorties d'outil arbitraires mais sans droit d'admission privilégiée.
- Clé individuelle compromise (agent, observateur, témoin ou guard), sans supposer que cela prouve une personne physique distincte.
- Instrument de mesure défectueux ou malveillant qui produit des rapports signés mais faux.
- Processus de journal ou de guard arrêté à n'importe quel point ; stockage local ou copie restaurée en arrière.
- Deux processus / hôtes partageant un fournisseur mais pas nécessairement le même verrou.
- Fournisseur pouvant retarder, dupliquer, partiellement appliquer ou omettre de confirmer une commande.
- Déployeur capable de modifier le runtime, les secrets ou l'identifiant de release selon son niveau d'accès.

## Frontières à qualifier

| Frontière | Entrée non fiable | Garantie à vérifier | Échec qui doit fermer |
|---|---|---|---|
| signature → identité | DSSE, WebAuthn, clés | sens signé unique, auteur réel dans la racine | signature/encodage/replay invalide |
| déclarations → loi | constitution du client | règles qui n'affaiblissent pas les floors | compilation ambiguë ou exception cachée |
| état → décision | préfixe signé, temps attesté | résultat/delta complet sur l'état exact | mutation silencieuse, droit indu |
| observateur → preuve | analyse externe | sujet, couverture, méthode, provenance exacts | déclaration auto-certifiée ou insuffisante |
| décision → journal | entrée candidate et pins | atomicité d'admission et reprise sûre | rollback, double-écriture, divergence |
| journal → départ | token, réservation, horloge | ordre correct des restrictions et de l'envoi | TOCTOU, réservation répétée |
| guard → fournisseur | requête, secret, endpoint | effet exact et unique ou inconnu explicite | autre endpoint, effet partiel, retry illégitime |
| exécution → clôture | retour fournisseur, observation | effet appliqué distinct de preuve d'exigence | succès déclaré sans vérification |
| release → exécution | code, dépendances, OS, CI | code réellement approuvé et pouvoirs exclusifs | import contourné, autre credential |

## Campagnes candidates (pas des résultats)

A01 — signer une loi équivalente en apparence mais moins restrictive.
A02 — horodatages proches du plafond et restriction simultanée.
A03 — même propriétaire humain sous deux identités logiques.
A04 — falsifier une affirmation de couverture « complete » avec ensemble incomplet.
A05 — scanner signant lui-même un résultat `reproduced` incorrect.
A06 — mutation invisible dans le delta.
A07 — crash avant/après ancre durable, journal et publication d'effet.
A08 — deux guards sous verrou local mais hôtes différents.
A09 — fournisseur reçoit une requête puis ne répond pas.
A10 — egress vers autre destination avec mêmes arguments logiques.
A11 — preuve d'application réutilisée pour un sujet différent.
A12 — retirer ou renommer une exigence sans régler son obligation.
A13 — run et bootstrap avec credentials de contournement.
A14 — mise à jour du code de confiance et confusion entre deux releases.
A15 — réconciliation d'un effet encore physiquement susceptible de partir.

## Première expérience reproductible

`python3 tcb_lab/experiments/g1_decision_probes.py`.

Elle observe quatre scénarios locaux sur **la véritable implémentation de main** et imprime un JSON ; elle ne démontre ni sécurité fournisseur, ni multi-hôte, ni complétude. Les résultats restent **NON TESTÉS** tant qu'une exécution n'a pas été observée.

Ne pas choisir de CIR, DSL, moteur de contrats ou algèbre avant consolidation des scénarios et causes racines.
