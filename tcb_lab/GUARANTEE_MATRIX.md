# G1 — Matrice initiale des garanties (audit de portée, pas preuve)

Référence : `main@d6347dccec714c0193bbc43af5de7e96e3a9ad27`. Statut des assertions : **CODE_OBSERVED** (structure identifiée), **EXTERNAL_ASSUMPTION**, **OPEN**, jamais « prouvé » sur la seule lecture.

| ID | Garantie attendue | Chemin de décision observé | Frontière d'application ou dépendance | Épreuve de complétude à construire | Statut |
|---|---|---|---|---|---|
| G01 | Aucun élargissement par un acteur seul | kernel._gate/_propose/_activate, floor0 | signature keys, root humaine, authentificateur | signataires distincts, clé compromise, collusion, rotation | OPEN |
| G02 | Révocation/gel immédiats face à l'expansion | kernel._gate/_freeze/_revoke/_unfreeze | admission durable, verrou et guard | restriction concurrente au départ, panne et plusieurs hôtes | OPEN |
| G03 | Loi cliente ne diminue pas floors | law.compose, kernel._law | release code pin, bootstrap | compilation sémantique, ancienne loi, migration | OPEN |
| G04 | Une entrée produit une transition canonique complète | kernel.decide/apply, invariants.check | admission Journal et runtime | dél tas malformés, mutation cachée, corruption | OPEN |
| G05 | Signatures liées au sens exact et à la genèse | crypto.open_envelope/verify | crypto backend, pin de la genèse | variantes WebAuthn/encodages, multiples clés physiques | OPEN |
| G06 | Le temps expire mais ne confère aucun droit | kernel checkpoint/anchor/last_at | quorum témoins, horloge de départ | horloges contradictoires, faux temps courant | OPEN |
| G07 | Preuve donnant permission qualifiée indépendamment | kernel._facts/_independent | scanner, oracle, identité physique des sources | données fausses mais signées, collusion, replay fraîcheur | OPEN |
| G08 | Obligation persistante et clôture fondée sur preuve | obligations.step, accountability | instruments, perte d'observation, auditeur | renommer/supprimer une cible, dette après reprise | OPEN |
| G09 | Aucun effet non jugé et départ revalidé | guard.redeem, judge_dispatch | credentials, adapter, API fournisseur | TOCTOU multi-hôte, egress détourné, double départ | OPEN |
| G10 | Réservation unique, effet inconnu réconcilié | floor0.LINE, kernel._reservation/_reconciliation | Journal SQLite, provider idempotency | crash entre réservation/send/retour, retry | OPEN |
| G11 | Historique non régressable avec reprise exacte | ledger.transact/recover_tail, pins | séparation stockage et restore domains | rollback coordonné journal + pin, crash boundary | OPEN |
| G12 | Second juge restreint et désaccord bloquant | invariants.check, ledger._judge | indépendance du code, évaluation de delta | faux positif/faux négatif, bug commun | OPEN |
| G13 | Attestation d'état n'est pas preuve d'effet | accountability.health, kernel._evidence | rapport externe, preuve fournisseur | preuve forgée / missing coverage / target false | OPEN |
| G14 | Aucun mode god à la genèse, run et récupération | genesis, floor0, bootstrap, recover_tail | processus de déploiement et clés de bootstrap | app initialement vide, import, migration, rotation | OPEN |
| G15 | TCB physique couvre chemins de contournement | guard, adapters/github, demo workflow | protection de branche, roles GitHub, tokens | inventaire exhaustif d'identifiants et de chemins mutateurs | OPEN |
| G16 | Système autonome non souverain | ops / scanner / tests / agent | provenance et isolement des preuves, CI | auteur = source, permissions latérales, fausse CI | OPEN |

**Observation critique :** G04 n'est pas identique à « chaque effet physique correspond à une transition » ; G09/G10 doivent être examinés indépendamment. Les contrats de preuve G07 et G13 ne peuvent pas être réputés remplis sur la seule existence d'un niveau `real`.

**Critère G1 :** pour chaque ligne, produire scénario reproductible, résultat vérifié, hypothèses d'attaque et décision de couverture. Aucun choix d'algèbre, de CIR ou de moteur de contrats avant ce travail.
