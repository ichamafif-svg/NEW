# vNext — première implémentation du noyau déterministe

Base : `main@d6347dccec714c0193bbc43af5de7e96e3a9ad27`.
Scope normatif figé : branche `research/tcb-scope-vnext`, fichiers `SCOPE.md` et `RESEARCH_PROTOCOL.md`.

Cette branche **contient l'ensemble du code de main** et ajoute une première surface d'exécution pure dans `vnext/decision.py`. Aucune compatibilité avec les anciennes genèses, formats ou API n'est imposée à la future implémentation. Le code historique sert de référence de garanties pendant la recherche.

## Réalisé

- `DeterministicCore.evaluate(state, signed_entry)` : entrée canonique, jugement constitutionnel réel issu de `main`, contrôle par le second juge indépendant, validation d'absence de mutation des arguments et calcul du delta sur une copie.
- `Decision` : résultat constitué d'octets immuables et de digests liés au code, à l'état avant/après, à la loi et à l'entrée.
- `preview` : projection du delta uniquement sur son prédécesseur exact, sans accès fournisseur ni persistance.
- `replay` : réduction déterministe des entrées avec une instance neuve du moteur par décision.
- `tests/test_vnext_decision.py` : déterminisme, absence de mutation, refus d'une restriction non autorisée, protection contre le rejeu d'un aperçu et entrées malformées.

## Limites et règles de sécurité

**Il s'agit d'une première extraction exécutable, pas d'un remplacement vNext certifié.** Les sept responsabilités constitutionnelles ne sont pas encore réimplémentées dans une abstraction neuve ; la sémantique héritée, y compris la couverture partielle du second vérificateur, demeure. L'infrastructure de confiance n'est pas remplacée.

Une `Decision` n'est **jamais** un mandat, un token, une réservation ou une autorisation d'envoi. Le journal et le guard de main restent les seuls chemins d'admission et d'effet physique existants.

Le nouveau dossier `vnext/` n'est pas couvert par le manifeste de confiance historique ; l'interface n'est donc pas activable en production sans définir une nouvelle chaîne d'amorçage, une nouvelle genèse et une frontière de contrôle exclusif. Aucune garantie de production additionnelle n'est revendiquée.

## Validation

Commande prévue : `python3 tests/test_vnext_decision.py`. La suite historique : `make check`.

**Tests vNext non exécutés dans l'environnement de création.** Ne pas confondre présence des tests et réussite de leur exécution. La suite de main n'a pas été exécutée à nouveau ici.

## Prochaine phase

1. Faire passer les tests et corriger les problèmes de frontière, sans patcher des symptômes de sécurité.
2. Formaliser la matrice des garanties historiques et les entrées/sorties des sept responsabilités.
3. Auditer la complétude du scope, en incluant la TCB effective et les composants de preuve externes.
4. Réaliser les recherches adversariales groupées, puis seulement rechercher une abstraction plus simple.
