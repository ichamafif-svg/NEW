# Noyau constitutionnel hybride de Standard

**Référence produit :** [Architecture de Standard](../STANDARD_ARCHITECTURE.md). **Statut : conception cible définie ; qualification de production non acquise.**

Le noyau garantit un **jugement déterministe unique** sur les sept responsabilités : **Identity, Authority, Law, State, Evidence, Obligation, Effect**. Ces responsabilités ne prescrivent ni sept moteurs ni une ontologie métier. Une constitution versionnée définit floors et loi client ; aucune règle client ne peut affaiblir les protections de la release.

## Principe interne

Une déclaration authentifiée et un préfixe d'état authentique entrent dans un système de relations typées et de contraintes finies. Le noyau établit l'autorité, qualifie les preuves déjà attestées par les frontières requises, dérive les obligations et le delta complet, puis rend un verdict reproductible. Aucun travail métier, réseau ou outil fournisseur ne s'exécute dans le jugement pur.

Une décision peut refuser, attendre une entrée qualifiée ou autoriser un **changement exact**. Les obligations demeurent indépendantes des WorkItems et des tentatives ; une clôture exige une preuve qualifiée. Une décision favorable n'est jamais un droit général d'appeler un fournisseur : l'effet est une intention bornée, contrôlée au départ par une garde exclusive.

## Architecture de confiance

- **K** : décisions de loi, autorité, preuve admissible, état, obligations et droits d'effet.
- **T** : ancrage de la release, indépendance des identités et des clés, temps, journal anti-rollback, vérification, qualification factuelle, egress privilégié, résultats et escalade.
- **U** : création, maintenance BUILD/RUN, diagnostics, scanners, plans, WorkItems, agents et adaptateurs d'infrastructure.

Standard s'intègre à l'outillage existant lorsque ses garanties sont suffisantes ; l'adaptateur ne devient jamais une autorité constitutionnelle par simple traduction de données.

## Contrats détaillés

- [Contrats d'implémentation](../IMPLEMENTATION_CONTRACTS.md) : responsabilité détaillée de chaque composant, invariants et tests d'acceptation.
- [Modèle conceptuel](KERNEL_CONCEPTUAL_MODEL.md) : objets, relations, transitions et invariants.
- [Trusted External](TRUSTED_EXTERNAL_CONTRACTS.md) : contrats physiques et domaines de confiance.
- [Protocole](KERNEL_EXECUTION_PROTOCOL.md) : admission, commit, effet et réconciliation.
- [Architecture globale](../STANDARD_ARCHITECTURE.md) : vision et surfaces produit.

## Validation

Le contrat conceptuel définit la cible, non sa preuve. Avant production il faut : vérifier l'autorité complète et la non-régression des floors, les obligations et preuves indépendantes, la reprise sans rollback, l'exclusivité du chemin d'effet, la seconde vérification, les tests d'incidents et de concurrence, ainsi que la tenue des objectifs de performance. **Tout déploiement non qualifié reste interdit.**
