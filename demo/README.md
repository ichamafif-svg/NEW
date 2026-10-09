# standard-demo

Un petit service de factures, volontairement imparfait, maintenu par des agents sous la loi signée de
[Standard](https://github.com/ichamafif-svg/NEW).

Au départ :
- dépendances vulnérables et en retard d'une version majeure ;
- un hachage MD5 pour les mots de passe et une clé d'API en dur ;
- des actions GitHub non épinglées et aucun SBOM.

Le workflow `standard` tourne toutes les six heures. Le scanner mesure, l'agent ouvre des pull requests, le guard
fusionne le commit exact que la loi admet, et le dossier de conformité est publié sur la branche `standard-journal`
(`report/dossier.html`).
