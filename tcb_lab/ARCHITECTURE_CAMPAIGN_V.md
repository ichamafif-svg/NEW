> **NOTE DE LECTURE — 2026-10-09.** Ce document conserve son contenu historique. Pour l'état **actuel**, consulter [l'accueil canonique](README.md), [la charte / transfert](LAB_CHARTER_AND_HANDOFF.md) et [la décision fonctionnelle 16/16](FUNCTIONAL_BOUNDARY_FREEZE_DECISION.md). Les étapes de comparaison architecturale A/B/C ou les verdicts 14/2 éventuellement mentionnés ci-dessous ne sont **plus** la feuille de route active. La production du noyau hybride est sur la branche `prototype/hybrid-kernel-v1`, non dans le lab ; les critères P3 physiques restent ouverts.

# Campagne V — recherche comparative d'architecture interne du noyau

**2026-10-09 · Étude pré-sélection, sans refactoring.** Source d'autorité : [découpage fonctionnel 16/16](FUNCTIONAL_BOUNDARY_FREEZE_DECISION.md) et [scope gelé](SCOPE.md). Les décisions d'implémentation sont **ouvertes**. Aucune architecture n'est gagnante par présomption.

## Question scientifique

Quel mécanisme de décision déterministe, total sur ses entrées admissibles et vérifiable avec une petite **TCB effective** satisfait les sept responsabilités sémantiques (Identity, Authority, Law, State, Evidence, Obligation, Effect) et les 16 garanties **sans internaliser les tâches U ni masquer les dépendances T** ?

### Trois hypothèses concurrentes

| Candidat | Hypothèse | Avantage à tester | Risque / falsificateur |
|---|---|---|---|
| A — moteur de transitions | Toute admissibilité et obligation résulte d'une transition canonique, produisant un delta exhaustif | Forte atomicité et audit de l'historique | Les qualifications indépendantes et obligations temporelles deviennent couplées au catalogue de transitions |
| B — moteur de contraintes | Des prédicats/invariants évaluent une transition candidate et sa variation d'état | Séparation des règles et facilité d'extension | Vérifier seulement « pas d'interdit » peut manquer un delta **requis** et laisser une obligation sans propriétaire |
| C — composition hybride | Invariants, transitions et obligations sont modélisés distinctement avec un jugement de composition atomique | Explicitation de chaque contrat et de son cycle de vie | Ordre d'évaluation, divergence de sémantiques et complexité d'un composant de plus |

**Attention :** B ne passe pas le contrat avec une simple validation locale d'invariants. Il doit valider *delta requis, interdit et exhaustif*. C ne passe pas par accumulation de composants : la composition doit rester déterministe, cohérente et vérifiable. A ne passe pas si la vérité externe ou la temporalité est artificiellement internalisée.

## Oracle commun, indépendant des candidats

La source de vérité d'un verdict n'est **pas** la sortie historique de `tcb/kernel.py` : elle découle des règles figées `SCOPE.md` et des allocations G01–G16. Dans [le corpus initial](experiments/architecture_oracle_cases.json), chaque entrée fournit un scénario, ses contraintes et le verdict/effet constitutionnel exigé.

Pour chaque candidat, distinguer les résultats : **ACCEPT / REJECT / PENDING_EXTERNAL / ESCALATION_DUE / UNRESOLVED**. `PENDING_EXTERNAL` désigne l'insuffisance d'une attestation ou d'un contrat T, **pas** une permission implicite. L'absence de capacité de déterminer la vérité externe est une limite établie et non un échec de calcul de K.

## Contrat minimal d'une évaluation

- **Input** : état canonique pré-transition, constitution et code épinglés, proposition authentifiée et assertions externes explicitement qualifiées ; temps transmis.
- **Output** : verdict déterministe, raison stable, delta complet et obligations créées/maintenues/fermées ; en cas d'effet, autorisation bornée en données, jamais en exécution directe.
- **Sans effet secondaire dans la décision** ; aucune lecture d'horloge ambiante, de GitHub, de secrets, d'un agent ou d'un réseau.
- **Monde extérieur** : les contrats des Trusted External sont des hypothèses décrites, jamais remplacées par une fausse oracle « vraie parce que signée ».

## Protocole de comparaison

1. **D0 : sens commun** — faire relire chaque verdict par deux analyses contradictoires ; contester les cas sous-spécifiés avant de coder.
2. **D1 : prototypes indépendants** — implémenter A, B, C avec le **même** contrat d'entrée/sortie sur des fixtures de taille comparable. Interdiction d'appeler le noyau historique comme oracle.
3. **D2 : différentiel** — mêmes scénarios et dérivations métamorphiques (réordonnancement de faits indépendants, réplication d'une preuve, révocation entre jugement et départ, changement de proposition sans changement de dette).
4. **D3 : adversarial** — chercher un contre-exemple qui casse une garantie, une complétude du delta, une preuve d'indépendance ou une frontière K/T/U.
5. **D4 : mesure** — rapporter nombre de composants de confiance, volume auditable, TCB effective, chemins d'autorisation, coût médian et p95 de la décision, taille des traces, complexité de migration. Aucun classement par lignes de code seules.

### Conditions de sélection

- **Barrières éliminatoires** : une seule garantie G01–G16 impossible à représenter ; décision dépendant d'un effet externe ; objet obligatoire perdu ; mutation spontanée ; preuve étrangère auto-validée ; delta partiellement contrôlé ; pouvoir souverain d'un agent.
- **Concurrence ouverte** : si plusieurs candidats satisfont les barrières, préférer celui qui minimise les **hypothèses de confiance et la complexité de vérification**, sous limites mesurées de performance. Si les données ne départagent pas les candidats, **ne pas choisir**.
- Revue indépendante de tous les contre-exemples avant arbitrage ; défauts du runtime/CI non attribués sans preuve au modèle étudié.

## Périmètre négatif

Pas de refactoring de `tcb/`, pas de choix CIR/DSL/algèbre, pas d'intégration Cloud/KMS/CI/SRE, pas de redéfinition G08/G16. Les campagnes historiques IV-I, G08/G16 et les problèmes physiques restent des audits d'implémentation/Trusted External, **non des conditions de démarrage ou d'arrêt de cette recherche d'architecture**.

## Livrables / gate

Le corpus d'oracles versionné, ses tests d'intégrité, trois prototypes comparables, matrice de contre-exemples, profil de performance, dossier de choix avec option « aucune », puis décision d'architecture *distincte du freeze fonctionnel*. **Statut actuel : CAMPAIGN_STARTED / CORPUS_INITIAL, NO_CANDIDATE_SELECTED.**
