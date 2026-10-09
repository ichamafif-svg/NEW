# KERNEL_CONCEPTUAL_MODEL — Modèle canonique du noyau hybride

**Statut : architecture conceptuelle candidate v1, cible production ; non certifiée.** Autorité du périmètre : [SCOPE.md](../tcb_lab/SCOPE.md) et [décision K/T/U 16/16](../tcb_lab/FUNCTIONAL_BOUNDARY_FREEZE_DECISION.md). Ce document n'étend pas le scope, ne choisit pas de DSL et ne prétend pas valider les Trusted External.

## 1. Invariant architectural

**Une décision constitutionnelle atomique, pas sept moteurs.** Les sept responsabilités Identity / Authority / Law / State / Evidence / Obligation / Effect sont des *axes sémantiques* vérifiés par un jugement unique. Le modèle métier est libre ; les primitives d'autorité restent fermées et versionnées.

`judge(snapshot, pinned_constitution, authenticated_statement, qualified_inputs) -> Decision` est une fonction pure et déterministe ; toutes les entrées sont canoniques, bornées et épinglées. `Decision` contient `verdict, reason, mandatory_delta, prohibited_delta_check, obligation_changes, effect_grant, trace_digest`. Aucune mutation et aucun I/O à l'intérieur de `judge`.

Trois catégories de sortie : `REJECT`, `PENDING` (fait ou preuve externe insuffisant, jamais autorisation), `ACCEPT` (mutation intégralement caractérisée). `ESCALATION_DUE` est une obligation/conséquence déterminable, pas un droit d'exécuter. Un verdict doit être stable pour des octets et un état épinglés identiques.

## 2. Les objets conceptuels, non les modules imposés

| Objet | Identité canonique | Relations essentielles | Invariant |
|---|---|---|---|
| Constitution | release + version + digest | floors, clauses client, primitives admises | Client ne peut affaiblir la release |
| Principal | domaine + id + provenance | holds, delegates, signs, witnesses | Une clé n'est pas une preuve d'humains distincts |
| Resource | espace de noms + id stable | subjectOf, requires, affectedBy | Le nom métier est opaque pour le noyau |
| Capability | id + parent + portée | holder, operation, resource, conditions, expiry | Toute délégation atténue les pouvoirs ; restriction a priorité |
| Claim | id + sujet exact + propriété | producedBy, coveredBy, qualifiesFor | Signature ≠ vérité ; fait non qualifié ne ferme rien |
| Obligation | exigence + sujet stable + génération d'écart | opened, due, requires, closedBy, escalatesBy | Essai échoué ≠ clôture ; retry ne remet pas due à zéro |
| Transition | déclaration signée + contexte + préfixe | reads, asserts, requires, changes, opens, closes | Delta complet, absence de mutation spontanée |
| EffectIntent | id + destination + payload digest + contexte | authorizedBy, reservedBy, dispatchedBy | L'intention n'est pas un dispatch et l'inconnu n'est pas un échec sûr |

Le **noyau n'inclut aucune ontologie GitHub, PR, scanner, SBOM, CI, fournisseur, WorkItem ou modèle IA**. Un adaptateur projette des entités externes vers des identités/relations typées via un contrat d'input ; il ne peut ajouter un fait constitutionnel par une simple conversion métier. Aucun « hard mapping » entre `resource.type` et un handler privilégié.

## 3. Modèle hybride : relations, contraintes, conséquences

1. **Relations typées et fermées sur leurs sémantiques d'autorité** : `holds, delegates, restricts, attests, qualifies, requires, closes, authorizes`. Les extensions peuvent ajouter des entités, qualificatifs et clauses métier validés, **pas redéfinir** `authorizes`.
2. **Contraintes** : prédicats purs, limités, typés et versionnés. Leur évaluation n'est pas une source de vérité externe.
3. **Transitions** : mutations proposées décrites avec `before` et `after`, vérification des champs *requis ET interdits*, génération complète du delta par le noyau.
4. **Obligations** : sous-ensemble du state canonique avec identité indépendante des tentatives ; créées et clôturées sous règles et attestations qualifiées.
5. **Effets** : autorisation *bornée* décrivant l'opération exacte ; son émission ne met pas le fournisseur à jour et ne donne pas un jeton général à l'agent.

Le jugement doit être total sur les entrées canoniques admissibles, avec rejets explicites pour valeurs/tailles/états non admis. Un module extérieur peut proposer une opération ou enrichir ses preuves, mais ne choisit pas la conséquence autorisée.

## 4. Séquence logique, une transaction

`canonicalize → validate pin/shape → validate statement & authority → qualify evidence/time → evaluate law/floors → derive mandatory obligations/effects → compare complete delta → produce verdict + trace`.

L'ordre des validations est normatif et doit être versionné : un changement d'ordre capable de modifier verdict/reason constitue un changement de sémantique. Une restriction déjà commise au préfixe de décision doit être prise en compte avant tout effet. Un jugement « accepté » ne court-circuite pas la vérification au départ.

## 5. Règles d'identité et de cycle de vie

- **Capability** : création gouvernée, atténuation monotone par délégation, révocation/gel sans élargissement implicite, expiration sans création de droits. Quorum, délais et témoins appartiennent à la loi du noyau.
- **Claim** : reçu, authentifié, lié au domaine et au sujet ; qualification séparée selon méthode, couverture, provenance, fraîcheur et indépendance ; invalidé ou expiré sans transformer « absence » en « sain ».
- **Obligation** : ouverture canonique, `due` stable pendant un même écart, tentatives multiples sans nouveau `opened`, clôture seulement par preuve qualifiée et transition explicitement autorisée ; changement de loi, migration et suppression d'exigence ont des issues distinctes de `repaired`.
- **EffectIntent** : proposé, autorisé, réservé, départ attesté, confirmé ou inconnu puis réconcilié. Aucun retry sur `unknown` ne doit être interprété comme « jamais appliqué ».

## 6. Invariants inter-objets à démontrer

- I1 : même préfixe et mêmes entrées → même verdict, même delta, même empreinte.
- I2 : aucune transition n'affaiblit les floors de la release.
- I3 : seul un changement explicitement gouverné peut élargir les pouvoirs.
- I4 : aucune admission ne ferme une obligation sur une simple déclaration de l'agent.
- I5 : une obligation ouverte survit au retrait, au retry et au remplacement des WorkItems.
- I6 : un effet ne sort que par une garde physique exclusive avec re-jugement et réservation.
- I7 : état et journal résistent à la restauration d'un préfixe ancien par une ancre indépendante.
- I8 : l'indépendance des vérificateurs n'est pas inférée du nombre de signatures.
- I9 : les conditions d'escalade sont décidables sous inputs fiables ; le scheduling réel est une hypothèse externe.
- I10 : le delta proposé ne peut omettre une modification obligatoire ni introduire une mutation arbitraire.

## 7. Réutilisation du dépôt et écarts actuels

| Code existant | Décision | Limite du prototype |
|---|---|---|
| `tcb/canon.py` | REUSE sous tests stricts | Canonicalité seulement, pas admission/authenticité |
| `tcb/crypto.py` | REUSE via port signé | Propriété de clé, identité physique, indépendance hors calcul |
| `tcb/policy.py` | REUSE puis EXTEND après contrat | Langage de prédicats borné ; ne décrit pas toute la loi |
| `tcb/obligations.py` | ADAPT plutôt que remplacer aveuglément | Cycle complet non porté dans hybride |
| `tcb/kernel.py` / `tcb/floor0.py` / `tcb/law.py` | EXTRACT contractual invariants | Pas de remplacement automatique de l'ancien noyau |
| `tcb/effects.py` / `tcb/guard.py` | REUSE contracts, auditer frontière | Exclusivité physique non démontrée par port Python |
| `hybrid_kernel/core.py` | PROTOTYPE only | `context.allowed` reçu, loi et obligations simplifiées, aucune gouvernance complète |

**Règle : ne pas confondre code existant et preuve de conformité.** Un composant retenu est soumis à des tests contradictoires sur les garanties qu'il prétend assumer. Les changements au modèle conceptuel requièrent un ADR et un oracle de non-régression G01–G16.

## 8. Décisions différées volontairement

Topologie des processus, langage d'implémentation final, algèbre/CIR/DSL, index de contraintes, optimisation incrémentale, stockage distribué, format métier des connecteurs. Aucun de ces choix ne doit réintroduire un mapping métier codé en dur ni un « deuxième noyau » externe.
