# Journal de consolidation documentaire — lab

**2026-10-09, IV-D.** Les références du laboratoire se lisent dans cet ordre :

1. [SCOPE.md](../SCOPE.md) : responsabilités **déjà figées**, sans déclaration de validation générale.
2. [EXPERIMENT_TREE_DEPTH_COVERAGE.md](../EXPERIMENT_TREE_DEPTH_COVERAGE.md) : couverture A/L/T/P/O/E/B/R × profondeur D0–D7 × frontière K/T/U ; les éléments testés, non testés et les limites restent distincts.
3. [TCB_BOUNDARY_MATRIX.md](../TCB_BOUNDARY_MATRIX.md), [ESTABLISHED_LIMITS.md](../ESTABLISHED_LIMITS.md) : 16 garanties et limites conditionnelles.
4. [IVB_BOUNDARY_CLOSURE.md](../IVB_BOUNDARY_CLOSURE.md) et [IVC_BOUNDARY_DECISIONS.md](../IVC_BOUNDARY_DECISIONS.md) : **14 délimitations conditionnelles / G08 et G16 sémantiquement ouvertes** ; classification, pas preuves physiques.
5. [P3_G08_G16_CAMPAIGN.md](P3_G08_G16_CAMPAIGN.md) : nouvelles expériences contrastées; [P3_LAB_STATUS.md](P3_LAB_STATUS.md) : tableau de bord textuel.
6. [Issue #2](https://github.com/ichamafif-svg/NEW/issues/2) : registre de résultats CI, le seul état machine actualisé automatiquement.

Les autres anciens rapports sont conservés comme **observations datées** : ils peuvent contenir des nombres / annonces antérieurs au dernier run, et ne doivent pas être lus comme statut actuel. Aucun ancien résultat n'a été supprimé, et aucun concept constitutionnel nouveau adopté. Le noyau, les règles et le scope demeurent intacts.

## Décision de consolidation — 9 octobre 2026 (statut actuel du **découpage**)

La [décision canonique de frontière fonctionnelle](../FUNCTIONAL_BOUNDARY_FREEZE_DECISION.md) attribue désormais **16/16 garanties G01–G16 à K (décisions du noyau), T (Trusted External) et U (autonomie remplaçable)** sous hypothèses explicites. **Statut : CONDITIONAL_BOUNDARY_FROZEN**, et **non** 16 garanties prouvées. Les anciennes mentions `14 conditionnelles / 2 ouvertes` ou `OPEN_SEMANTIC` pour G08/G16 décrivent **l'étape IV-C/IV-D historique** et sont supplantées **uniquement pour la délimitation fonctionnelle** ; elles restent utiles comme état des preuves à leur date. G08 : dette canonique indépendante des tentatives ; G16 : règles de permission, dette et exigibilité d'escalade dans K, scheduling/retries/notification dans U et préconditions fiables dans T. La campagne IV-I et les travaux d'implémentation ne bloquent **pas** la décision de découpage. Le scope sémantique `SCOPE.md` demeure intact ; l'assurance physique, l'audit de déploiement et les portes de sortie P3 restent **ouverts**. Ne pas relancer une boucle de recherche sur tout Standard sans contre-exemple démontrant une mauvaise attribution K/T/U.
