# Standard — TCB vNext : périmètre figé

Cette branche repart d'un **arbre source neuf**. Elle n'embarque volontairement ni l'ancien runtime, ni ses tests, ni ses documents. Le commit de départ conserve un ancêtre Git de `main` pour la traçabilité, mais **aucune compatibilité de code, de format, de journal, de genèse ou d'API n'est requise**.

**Référence historique :** `main@d6347dccec714c0193bbc43af5de7e96e3a9ad27`.
**Statut :** périmètre fonctionnel et protocole de recherche figés ; **aucun noyau vNext implémenté, aucune garantie vNext démontrée**.

Lire `SCOPE.md` (contrat normatif) et `RESEARCH_PROTOCOL.md` (portes de validation et méthode adversariale).

La nouvelle implémentation devra établir une garantie **au moins aussi forte, propriété par propriété**, que la base historique. Les garanties revendiquées mais jamais établies devront être distinguées des garanties prouvées ; les limitations ne peuvent pas être masquées par une nouvelle abstraction.
