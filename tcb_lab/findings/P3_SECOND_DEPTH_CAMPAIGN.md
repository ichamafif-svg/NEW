# Phase 3 — deuxième campagne PROFONDEUR × COUVERTURE (P1/E1/O1)

**Scope inchangé.** Aucun test ne définit une abstraction. Les résultats ont priorité sur le nombre de cas et sur la couleur globale d'Actions.

## Arbres effectivement instrumentés

| Arbre | Instrument | Contrastes | Dimension explorée | Limite à respecter |
|---|---|---:|---|---|
| **P1** preuve trompeuse | `p3_depth_proof.py` | 7 | auteur de l'attestation, sujet, grade annoncé, signature correcte, temps décalé, vérité indépendante connue de la fixture | pas de vérité fournisseur attestée ; le drapeau de vérité est un contrôle synthétique |
| **E1** effet incertain | `p3_depth_effect.py` | 8 | `unknown`, `ok`, `failed`, exception post-envoi ; deuxième redeem même guard/autre journal | même SQLite, pas deux hôtes, pas de fournisseur réel |
| **O1/R1** continuité | `p3_depth_autonomy.py` | 16 | 10 reprises rouges identiques, 3 variantes rouges plus longues, 3 contrôles `none` | variation inter-fixture et conditions non déterministes non entièrement isolées |

La CI lance les trois suites et conserve les observations même si d'autres scénarios échouent. Pour chaque étape, l'oracle est `OBSERVED` ou `INCONCLUSIVE` : **OBSERVED n'est pas synonyme de propriété satisfaite**. Une divergence d'observation doit être examinée avant toute qualification de vulnérabilité.

## Décisions expérimentales ouvertes après cette campagne

**P1.** La fausse attestation signée fermait la dette dans la première campagne. La deuxième discrimine le type d'auteur, le mauvais sujet, le niveau de preuve et une anomalie temporelle. Si un grade inconnu ferme néanmoins une dette, documenter les exigences effectivement appliquées ; si seul le bon grade est admis, ne pas confondre grade et véracité. Suite : fraîcheur et couverture attestées depuis un oracle externe indépendant.

**E1.** Deux handles de journal contre le même fichier SQLite peuvent confirmer une réservation locale, mais jamais un fencing inter-hôte. Une double tentative de redeem bloquée ne prouve pas que le fournisseur n'a pas appliqué plusieurs fois une requête sous timeout. Suite : injection de crash ordonnée entre réserve, send, ACK et preuve.

**O1/R1.** Les runs rouges historiques et le premier redémarrage vert ne démontrent ni une régression permanente ni une absence de faute. La répétition à SHA identique fournit une base pour localiser les variations. Suite : conserver les préfixes de sujets et les obligations avant/après chaque cycle pour départager effet de simulation et comportement constitutionnel.

## Couverture des autres findings

Ne pas perdre les six feuilles restantes du backlog : O1 deadline même sujet ; L/E changements de loi au départ ; T/B pin-journal restore ; A/P possession indépendante des oracles ; E/B deux domaines de panne ; R autonomie BUILD/RUN. Toutes restent **non clôturées** ; aucune profondeur D5–D7 n'est validée sur ces tests locaux.

## Journal de runs

Rapport vivant : https://github.com/ichamafif-svg/NEW/issues/2. Ce document est le plan d'attaque exécuté ; toute conclusion de résultat devra donner **run, commit, observations individualisées et hypothèses**.
