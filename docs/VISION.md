# Standard : vision et contrat d'architecture

Standard permet à des agents de construire puis surtout de maintenir un dépôt sous une loi vérifiable, sans leur confier l'autorité de décider seuls ce qu'ils ont le droit de faire. Le service géré est le produit ; la TCB est son socle de confiance.

Le travail vient de la différence entre les exigences applicables et les preuves disponibles. L'autonomie vient des capacités accordées pour traiter ce travail. Une obligation ne crée jamais une permission. Un manque de couverture reste un écart ; une escalade ne prouve ni réception, ni réponse, ni réparation.

## Loi et adoption

| Couche | Fonction | Changement |
|---|---|---|
| FLOOR-0 | Autorité, causalité, polarité, historique, preuve et passage aux effets | Release proposée par Standard, explicitement adoptée par le client |
| Floors | Exigences communes et mesurables | Même adoption de release ; le client ne peut pas les affaiblir |
| Loi client | Identités, contexte, exigences supplémentaires et resserrements | Quorum, délai attesté, activation explicite dans le journal |

La version actuelle ne migre pas une release dans un journal existant. Une nouvelle genèse demande une sélection externe du code et de la loi. Une mise à jour de Standard ne remplace pas automatiquement ce choix. Modifier une loi client utilise le protocole gouverné même quand la modification envisagée resserre seulement les exigences.

## Boucle produit

1. Des sources observent le périmètre déclaré et proposent des faits signés.
2. Le noyau admet les entrées selon la loi et le préfixe déjà admis.
3. La redevabilité dérive les écarts, échéances et escalades.
4. La maintenance transforme ces vues en propositions de travail.
5. Un agent prépare une solution puis propose une intention signée sous une capacité existante.
6. Le passage physique réserve, rejuge et envoie l'effet typé.
7. Une source indépendante atteste le résultat ; seule la preuve admise peut satisfaire le contrat de clôture.

M2 réalise une partie de cette boucle sur des transitions `base → head` : tests de la base, recettes reproductibles ou revue du head, réservation et fast-forward. Les cinq contrats complets de `COEUR-STABLE.md` restent la cible ; ils ne sont pas tous réalisés.

Les étapes de préparation, de sélection du travail et de présentation peuvent être riches et faillibles. Elles ne contournent jamais l'admission. La construction d'un dépôt vide utilise les mêmes contrôles : BUILD ne donne pas carte blanche. Le passage à RUN se caractérise par les cibles et les preuves de préparation, pas par une exemption générale de sécurité.

## Frontières

| Couche | Autorité permise | État actuel |
|---|---|---|
| Noyau | Jugement déterministe et delta d'état ; aucune action physique | Présent ; initialisation du digest et caches distincts du jugement |
| Intégrité | Conserver le préfixe admis et ses épingles ; bloquer un désaccord | Présent |
| Effets | Au plus une tentative locale par réservation, requête canonique rejugée | Présent ; adaptateur GitHub fast-forward, garanties de déploiement conditionnelles |
| Redevabilité | Lire, dériver et exposer des preuves manquantes | Présente et confinée ; langage fini actuel |
| Maintenance | Proposer du travail ou une revue humaine | Projection en lecture seule dans `maintenance/`, cycle opérationnel M2 dans `ops/` |
| Sources, agents et interface | Préparer des propositions et les faire signer par les identités autorisées | Recettes, instruments, agent et workflow de démonstration ; service géré complet non livré |

`maintenance/` n'est pas importé par la TCB. Il ne reçoit ni journal mutable, ni signataire, ni credential. Sa sortie n'est pas une preuve et ne ferme rien. Il peut être remplacé sans changer le code épinglé. Un plan erroné peut mal prioriser ou masquer du travail dans une interface : la vue canonique reste celle de l'auditeur épinglé et doit être accessible séparément.

## Garanties conservées

- Restrictions limitées aux identités et périmètres autorisés ; maintien du veto et de son dépassement gouverné.
- Élargissement explicite après quorum et délai ; le temps seul n'accorde rien. L'absence de fait n'autorise rien.
- Épingle après jugement réussi, avant commit visible et avant acquittement ; restauration exacte de la queue après interruption.
- Recontrôle indépendant des effets et refus sur désaccord. « Aucun bug seul » reste un objectif partiellement couvert, pas un théorème global.
- Contrats de conditions, opérations, cibles et OBL épinglés. Une nouvelle règle ne transforme pas une ancienne preuve en preuve de réparation.
- Une tentative locale unique n'est pas une garantie universelle d'effet distant unique ; le fournisseur doit honorer la clé de déduplication.

CAP, OBL, NIV, PROV, TYPE et HIST désignent les primitives du modèle. Leur suffisance pour toute règle métier n'est pas démontrée. La provenance est une indépendance de chaînes de détenteurs ; l'enrôlement doit établir l'indépendance réelle des personnes et organisations.

## Capacités à construire hors du cœur

Les floors actuels déclarent inventaire, huit mesures techniques, protection de main, lignée et attestations organisationnelles. M2 fournit des sondes Python, des recettes et un adaptateur GitHub ; leur présence ne démontre pas des garanties complètes SRE, sécurité et conformité. La conformité réglementaire ne se déduit pas d'un simple statut PROVEN.

Les intégrations doivent reprendre la CI, l'IAM, les scanners et les procédures du dépôt, exprimer leur rôle dans la loi et vérifier leurs contrats. Elles doivent rendre visible ce qui manque. Toute intégration capable d'un effet physique reste dans le périmètre de confiance et dans le budget ; déplacer un adaptateur hors de `tcb/` ne le rend pas non fiable.

Un langage de redevabilité plus riche pourra produire des vues et propositions. Toute portion de calcul utilisée pour accorder un droit ou satisfaire une clôture qui débloque une action doit rester contrôlée dans la TCB. Les témoins externes sont une évolution distincte : quorum de domaines indépendants, contrat temporel explicite et comportement en panne restent à définir. Le hold ne remplace pas le veto à garantie constante.

## Présentation humaine

L'interface met en avant le périmètre maintenu, les preuves manquantes, les échéances, les restrictions et les décisions attendues. Les détails de signatures, contrats et historique restent accessibles. PROVEN porte sur les cibles déclarées au préfixe et à l'horizon nommés ; FAULT reste visible, jamais transformé en « sain ».

## Critère de prochaine refonte

Le plafond de sûreté reste 2 942 lignes, avec deux budgets distincts de 537 lignes restrictives et 500 de visibilité. Le résultat courant est dans `validation/summary.json`; les 3 244 lignes et le blocage V6 sont historiques. Toute nouvelle abstraction doit conserver les scénarios adversariaux exécutables et déclarer les dépendances communes. Les règles métier se développent par déclarations et intégrations ; les mécanismes de confiance ne doivent pas croître au même rythme. Aucun comptage artificiel ni déplacement de code de confiance ne constitue une réduction.
