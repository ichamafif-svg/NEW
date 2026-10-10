# Validation locale du noyau hybride

`results.json` contient les comptes de lignes, 213 tests, le différentiel et les 26 campagnes exécutées. `make-check.log` conserve les sorties des tests. `differential.json` conserve les résultats de comparaison.

Le différentiel rejoue les transitions signées avec un interpréteur de référence chargé uniquement en mémoire pour les tests ; il partage les primitives de loi et de cryptographie épinglées et ne valide pas les extensions natives. Les injections volontairement corrompues du moteur sont isolées du comptage d'équivalence et restent testées par le contrôle AND. Pour le rejouer, rendre le commit de référence disponible dans Git et lancer `python tools/compare_kernel_reference.py`.

Les 26 campagnes ont produit des refus conditionnels et des observations attendues. Une sortie `OBSERVED` n'est pas une certification. Les Trusted Externals et la migration de release restent soumis à qualification/gouvernance ; aucune déclaration de production n'est générée.
