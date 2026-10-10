# standard-demo

Service de factures volontairement imparfait : dépendances anciennes, MD5, secret en dur, actions non épinglées et SBOM absent. Il sert de sujet de maintenance ; il n'est pas un service à déployer comme référence de sécurité.

Le workflow fourni suit le cycle M2 actuel : instruments sans clés Standard → checkpoint → scan signé → checkpoint → agent → checkpoint → guard → rapport. L'agent prépare une transition `base → head`; il n'ouvre plus de PR. Les recettes reproductibles avec tests verts peuvent satisfaire la condition autonome ; les autres changements demandent une revue signée `review --head SHA`.

Pour l'utiliser dans un dépôt séparé, adopter `STANDARD_REF` (SHA de release) et une nouvelle `STANDARD_GENESIS`, créer les environnements et leurs secrets/Apps selon [docs/M2.md](../docs/M2.md), puis amorcer l'état signé. Le workflow refuse un pin absent ou non immuable. La programmation toutes les six heures ne démontre pas que ces paramètres sont configurés ni que le fournisseur autorise l'effet.

Les branches `standard-journal` et `standard-pins` transportent l'état et le dossier (`report/dossier.html`). Leur stockage après les effets reste une limite de durabilité ; le workflow n'est pas une architecture de production. Les protections guard-only, le temps, l'egress et le confinement du runner restent à établir.

Sur la branche du noyau hybride, `tcb.Kernel` est un import de compatibilité du seul
`hybrid_kernel.core.Kernel` : le cycle ci-dessus passe déjà par son jugement unique.
Le rapport produit aussi `report/constitution.md`, qui lie la loi **effective**
(floors + loi client), les obligations et les écarts de qualification T au même
préfixe. L'agent reçoit une projection textuelle contextualisée en lecture seule pour une réparation préparée
par modèle. Les sondes M2 connues lisent les cibles effectives, y compris les
resserrements clients ; les nouvelles cibles métier n'ont pas encore d'instrument
ni de route M2 générique. Le scanner refuse un fichier de mesures lié à une autre
loi et demande une nouvelle mesure. Une attestation T absente ou une ligne `UNVERIFIED_PHYSICAL` du
manifeste ne devient jamais une permission ni une preuve physique ; ces écarts
orientent la qualification indépendante. Le cycle de démonstration continue
cependant d'utiliser un stockage Git et un adaptateur locaux sans isolation
physique qualifiée : il ne constitue pas le déploiement `GovernedDeployment`.
