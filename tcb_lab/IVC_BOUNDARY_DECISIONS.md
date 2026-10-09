# Campagne IV-C — Fermeture conditionnelle des 12 frontières ouvertes

**9 octobre 2026 · Décision de recherche, non preuve de déploiement.** Le contrat sémantique de [SCOPE.md](SCOPE.md) demeure figé. `CLOSED_CONDITIONAL` signifie uniquement que les responsabilités sont délimitées avec des hypothèses falsifiables, **pas** que le déploiement tient la garantie. `OPEN_SEMANTIC` signifie que la propriété elle-même reste insuffisamment définie. `BLOCKED_PHYSICAL` signifie que seul un test d'infrastructure réelle permet de qualifier l'implémentation.

## Douze frontières — clôture du *découpage* et blocages de la *démonstration*

| ID | Noyau pur — obligation non délégable | Contrat externe indispensable | Contre-expérience nécessaire | Découpage | Déploiement |
|---|---|---|---|---|---|
| G02 | Restriction immédiate dans l'ordre logique, re-jugement au départ | Ordre atomique admission/révocation/départ, aucun canal alternatif | Révoquer pendant réservation et avant les octets physiques | CLOSED_CONDITIONAL | BLOCKED_PHYSICAL |
| G05 | Signatures liées au domaine et au contenu, seuil logique | Garde des clés, association vérifiée personnes/identités, runtime authentique | Même acteur possédant deux clés de quorum | CLOSED_CONDITIONAL | BLOCKED_PHYSICAL |
| G07 | Vérifier sujet, méthode, couverture, fraîcheur et source habilitée | Mesure réelle, intégrité de l'univers et indépendance des observateurs | Bonne signature sur couverture mensongère | CLOSED_CONDITIONAL | BLOCKED_PHYSICAL |
| G08 | Maintenir identité d'exigence, sujet, dette et échéance durant tout écart continu | Journal durable et observations exploitables sur les changements de cible | 100 retraits et renommages, aucune réinitialisation de dette | OPEN_SEMANTIC | OPEN_SEMANTIC |
| G09 | Autoriser/rejuger le contrat exact de l'effet | Exécutant exclusif, credentials isolés, octets vérifiés | Second writer avec autre token et autre entrée | CLOSED_CONDITIONAL | BLOCKED_PHYSICAL |
| G10 | Consigner réservation, statut inconnu, blocage et conditions de réconciliation | Idempotence/fencing, readback fiable, garantie de livraison observable | Crash après application et avant ACK, nouvel acteur | CLOSED_CONDITIONAL | BLOCKED_PHYSICAL |
| G11 | Refuser un préfixe incompatible avec son ancre | Pin durable indépendant du domaine restauré | Rollback coordonné journal et pin | CLOSED_CONDITIONAL | BLOCKED_PHYSICAL |
| G12 | Exiger juge restreint et bloquer tout désaccord | Vérificateur effectivement indépendant des défauts critiques | Deux juges approuvant la même proposition fausse | CLOSED_CONDITIONAL | BLOCKED_PHYSICAL |
| G13 | Ne fermer que sur preuve admissible ciblée, distincte du résultat d'exécution | Véracité et exhaustivité de la mesure | Scanner mensonger, univers tronqué, clôture induite | CLOSED_CONDITIONAL | BLOCKED_PHYSICAL |
| G14 | Gouverner genèse, changement, récupération sans privilège unilatéral | Installation, pin de code, clés et root indépendants | Ancien binaire ou restore god-mode avec secrets réutilisés | CLOSED_CONDITIONAL | BLOCKED_PHYSICAL |
| G15 | Définir et contrôler le contrat d'effet sur l'ensemble des interfaces déclarées | Exclusivité OS/réseau/API, inventaire des chemins mutateurs et secrets | Job CI hors guard avec secret write | CLOSED_CONDITIONAL | BLOCKED_PHYSICAL |
| G16 | Maintenir les règles d'obligation, de permission et d'escalade sans agent souverain | Agents/scanners/ordonnanceurs disponibles et observables | WorkItems ratés, gap permanent, zéro progrès ni escalade | OPEN_SEMANTIC | OPEN_SEMANTIC |

**Synthèse :** sur les 12 frontières auparavant ouvertes, **10 allocations** peuvent être formulées conditionnellement (par séparation calcul/monde), tandis que **G08 et G16** demandent toujours de départager les sémantiques de continuité et de progression. Les dix frontières conditionnelles ne sont **pas validées physiquement**. Avec les quatre conditions déjà décrites dans IV-B, cela donne **14 allocations conditionnelles / 2 frontières sémantiques ouvertes**, mais **aucune conclusion de sûreté globale**.

## Pourquoi les dix allocations peuvent être conditionnelles

La classification ne vient pas d'une exécution du fournisseur. Elle découle de la limite de capacité et d'information du calcul pur : le noyau peut juger une représentation canonique ; il ne peut ni attester la vérité physique absente, ni empêcher un exécuteur caché muni de credentials, ni rendre durable à lui seul une donnée supprimée dans tous les domaines de restauration. L'exigence extérieure appartient à la **TCB effective** et doit posséder un contrat vérifiable avant toute promesse produit. Cette frontière logique est acceptable ; une implémentation externe non vérifiée ne l'est pas.

## Deux lacunes sémantiques bloquantes

**G08 — Continuité de dette.** Définir sans technologie (a) la notion de *même écart* à travers noms, versions et tentatives, (b) le témoin d'ouverture de dette, (c) la condition exacte de clôture et (d) ce qui empêche un reset d'échéance arbitraire. Les anciennes séries sur des ressources distinctes ne répondent pas à cette question.

**G16 — Autonomie non souveraine.** Énoncer la propriété de progrès *conditionnelle* : si les sources externes requises restent disponibles, si une action permise existe et si l'ordonnancement est équitable, le système doit soit réaliser une transition observable, soit produire une escalade explicite dans une borne définie. Sans hypothèses d'équité/disponibilité, une liveness absolue est impossible. Il reste à mesurer blocages, retries et escalades.

## Expériences discriminantes suivantes

1. Tracer un sujet unique 20 et 100 fois, avec identité du gap, `opened`, `due`, retraits, preuves et raison de nouvelle proposition ; oracle positif et négatif.
2. Injecter deux acteurs concurrents sur même ressource avec délais d'exécution, puis perte d'ACK, en séparant **résultat logiciel** et **reçu provider**.
3. Fournir preuves avec **contenus réellement différents** et source d'observation indépendante ; prouver que qualifier une source ne revient pas à l'autoriser à décider.
4. Forcer restore de journal et pin dans deux domaines de panne, rechercher les permissions latérales CI/OS/API et les fausses indépendances de clés et de juges.

## Porte de sortie

**Scope sémantique antérieur : FROZEN (unchanged).** **Délimitation : 14 CLOSED_CONDITIONAL / 2 OPEN_SEMANTIC.** Ce résultat reste une **classification raisonnée**. Ne pas annoncer que 14 garanties sont prouvées, ni que toutes les exigences des limites externes sont satisfaites. Le passage à une recherche d'abstractions requiert une revue contradictoire des deux sémantiques ouvertes et du contrat de confiance effectif, avec chacun de ses `BLOCKED_PHYSICAL` explicitement porté vers la validation système.

## Décision de consolidation — 9 octobre 2026 (statut actuel du **découpage**)

La [décision canonique de frontière fonctionnelle](FUNCTIONAL_BOUNDARY_FREEZE_DECISION.md) attribue désormais **16/16 garanties G01–G16 à K (décisions du noyau), T (Trusted External) et U (autonomie remplaçable)** sous hypothèses explicites. **Statut : CONDITIONAL_BOUNDARY_FROZEN**, et **non** 16 garanties prouvées. Les anciennes mentions `14 conditionnelles / 2 ouvertes` ou `OPEN_SEMANTIC` pour G08/G16 décrivent **l'étape IV-C/IV-D historique** et sont supplantées **uniquement pour la délimitation fonctionnelle** ; elles restent utiles comme état des preuves à leur date. G08 : dette canonique indépendante des tentatives ; G16 : règles de permission, dette et exigibilité d'escalade dans K, scheduling/retries/notification dans U et préconditions fiables dans T. La campagne IV-I et les travaux d'implémentation ne bloquent **pas** la décision de découpage. Le scope sémantique `SCOPE.md` demeure intact ; l'assurance physique, l'audit de déploiement et les portes de sortie P3 restent **ouverts**. Ne pas relancer une boucle de recherche sur tout Standard sans contre-exemple démontrant une mauvaise attribution K/T/U.
