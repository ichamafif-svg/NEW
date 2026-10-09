# Phase 3 — Modèle adversarial de l'autonomie gouvernée

## Promesse produit à tester

Standard sert à **faire construire et surtout maintenir un dépôt par des agents IA**, en faisant respecter une loi que les agents ne contrôlent pas. Une TCB qui refuse toute opération satisfait trivialement certaines propriétés de sécurité, **mais échoue à l'objectif du produit**. Inversement, une IA pouvant tout exécuter paraît autonome, mais échoue à l'objectif constitutionnel.

Tester en permanence les **deux faces d'une garantie** :
- **Safety :** aucune transition ou effet interdit, aucune preuve fictive, aucune suppression arbitraire des obligations.
- **Progress sous hypothèses explicites :** lorsqu'il existe une capacité valide, une preuve accessible, un fournisseur disponible et une voie de réparation permise, le système peut progresser sans approbation humaine inutile. Si ces hypothèses échouent, l'incident doit rester identifiable et déclencher une issue sûre (attente, obligation stable, escalade).

Une garantie de progrès est généralement **conditionnelle** : elle ne peut pas promettre l'exécution malgré une indisponibilité permanente d'un humain requis, d'un témoin, d'un fournisseur ou d'un stockage externe. Les hypothèses de disponibilité doivent être écrites.

## Cycle autonome minimal comme banc d'essai

`observe → detect_gap → open_obligation → authorize_agent_work → propose_change → qualify_evidence → reserve → rejudge → dispatch → reconcile → prove_effect → verify_target → discharge_or_escalate`

Cette chaîne n'est **ni** un IR ni une liste de modules obligatoires ; c'est un scénario de bout en bout servant à tester toutes les abstractions candidates. Le noyau ne doit pas absorber les algorithmes de scanning, de coding ou de planification. Il doit en contrôler les déclarations et effets qui font autorité.

## Propriétés bi-directionnelles à éprouver

| Propriété | Attaque safety | Attaque progression/autonomie |
|---|---|---|
| Autorité | agent sans grant exécute | agent avec grant valide reste bloqué sans motif |
| Restrictions | effet malgré gel/revoke | levée autorisée et différée jamais activable |
| Temps | token périmé passe | horloge bloquée suspend indéfiniment toute maintenance sans diagnostic |
| Loi | client affaiblit floor | loi valide impossible à appliquer pour une erreur d'interprétation |
| Preuves | agent auto-certifie | preuve valide rejetée sans raison falsifiable |
| Obligations | réparation ratée clôt la dette | deadline relancée infiniment par WorkItems |
| Effets | double départ / mauvais endpoint | effet refusé après succès de toutes conditions vérifiées |
| Reprise | crash rejoue effet incertain | crash laisse une obligation inobservable et irréparable |
| Infrastructure | autre credential bypass guard | absence de credentials attendus interprétée comme succès |
| Conformité | audit déclaratif vaut preuve technique | exigence organisationnelle impossible à escalader |

## Mesures proposées au laboratoire

**Safety violations (SV)** : nombre de violations reproductibles du contrat de permission et de transition, sans comparer superficiellement le nombre de tests verts.

**Progress failures (PF)** : nombre d'impasses injustifiées malgré préconditions valides, et distinction avec des arrêts conservateurs **exigés** par la loi.

**Indeterminate effects (IE)** : réservations envoyées à effet inconnu, proportion réconciliée par preuve indépendante, et démonstration qu'aucun retry dangereux ne démarre entre-temps.

**Obligation continuity (OC)** : persistance des dettes à travers échecs, redémarrages, renommages, expirations et changement de loi; suivi de l'échéance originale.

**Privilege boundary (PB)** : liste complète des credentials, propriétaires physiques, canaux d'egress et exemptions ; tests des chemins d'exécution alternatifs.

**Evidence soundness (ES)** : précision du sujet/commit/ressource/méthode/univers ; capacité des observations mensongères, partielles ou auto-certifiées à déverrouiller une action.

## Couverture actuelle et besoins ouverts

`p3_autonomy.py` contient dix exercices locaux de sécurité et progrès portant sur les intentions, délégations, restrictions, vérification après effet et quotas. `p3_effect_line.py` explore concurrence locale, incertitude et preuve indépendante ; `p3_mutation_fuzz.py` explore trente mutations signées.

Les 80 hypothèses supplémentaires dans `ATTACK_EXPANSION.md` doivent guider les autres harnais de test. En particulier **CI fluctuante, obligations stables, découverte d'un repo vide, système SRE préexistant, agents multiples, absence d'escalade humaine** restent des risques à instrumenter. Ces sujets constituent des frontières TCB lorsqu'ils conditionnent permission/preuve/effet, mais non une invitation à coder la plateforme d'orchestration dans ce laboratoire.

**Ne pas optimiser l'autonomie en affaiblissant FLOOR-0.** Chercher des abstractions qui suppriment les erreurs d'autorisation **et** diminuent les impasses injustifiées, sans déplacer des hypothèses de confiance hors de la matrice.
