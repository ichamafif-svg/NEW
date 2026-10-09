# Trusted External — contrats de confiance de Standard

**Statut : frontières fonctionnelles définies ; conformité physique à démontrer par déploiement.** Les neuf contrats sont des responsabilités vérifiables, **pas neuf microservices imposés**. Ils constituent avec le noyau la TCB effective.

## Pourquoi une fonction est Trusted External

Une dépendance est T si sa compromission peut fabriquer l'identité/autorité réelle, falsifier une preuve prise pour recevable, restaurer un état constitutionnel ancien ou émettre un effet privilégié interdit. Une couche de planification sans privilège reste autonome non souveraine (U). Le noyau (K) est seul compétent pour interpréter les conséquences constitutionnelles.

## Catalogue

| Contrat | Garantie nécessaire | Défaillance à contenir |
|---|---|---|
| T01 — Trust anchor | Release, constitution, runtime et genèse authentiques | Substitution, downgrade, re-genèse |
| T02 — Identity & key custody | Liens entre identités, clés et individus réellement distincts | Clés compromises, faux quorum |
| T03 — Trusted time | Temps attesté, fraîcheur et bornes d'incertitude | Horloge manipulée, délais contournés |
| T04 — Durable ledger | Ordre atomique, stockage vérifiable et anti-rollback indépendant | Restaurations, réécriture, préfixe supprimé |
| T05 — Independent verifier | Vérification réellement indépendante des transitions critiques | Bug ou contrôle commun non détecté |
| T06 — Evidence attestor | Méthode, couverture, provenance, sujet et indépendance des faits | Mesure mensongère mais signée |
| T07 — Effect guard | Credentials exclusifs, destination et octets exacts, revalidation, fencing | Egress parallèle ou effet altéré |
| T08 — Effect reconciler | Réservation, identité d'opération, ACK/readback et état UNKNOWN | Retry aveugle d'une action possiblement appliquée |
| T09 — Progress/escalation | Signaux, livraison et accusés conformes aux hypothèses de disponibilité | Dette ou escalade due non délivrée |

Un fournisseur peut satisfaire plusieurs contrats s'il prouve les propriétés requises. La séparation de services sous un même compte administrateur n'est pas une indépendance physique. Le déploiement doit documenter dépendances communes, acteurs, clés, capacités de restauration, secrets et chemins d'egress.

## Contrat d'interface commun

Chaque capacité de confiance expose : identifiant et version du contrat, domaine d'autorité, sujet exact, opération, digests d'entrée/sortie, identité de l'attestateur, validité temporelle, qualité de provenance, couverture et état de vérification. Les états `REJECTED`, `UNAVAILABLE` ou `INDETERMINATE` ne donnent jamais une permission implicite.

L'attestation cryptographique prouve une origine sous ses hypothèses ; elle ne prouve pas automatiquement la véracité physique, l'indépendance des personnes ni l'exhaustivité d'une couverture.

## Frontières de défaillance

- Si une racine d'identité ou un ancrage n'est pas fiable, les opérations constitutionnelles sensibles sont bloquées.
- Un ledger ne prouve pas sa propre inviolabilité : son anti-rollback dépend d'un domaine indépendant.
- Une autorisation logique n'exécute rien ; seul le garde d'effets possède la sortie privilégiée.
- Un résultat fournisseur inconnu reste `UNKNOWN` jusqu'à preuve suffisante.
- Les vérificateurs exigés ne doivent pas partager un domaine de panne qui annule l'indépendance promise.
- K constate l'exigibilité d'une escalade ; les garanties de livraison reposent sur une disponibilité physique explicitement définie.

## Qualification de production

Pour T01–T09, consigner le fournisseur, la version, la frontière de restauration, les identités/permissions, le modèle de menace, les tests contradictoires, le comportement fail-closed et les limites réelles. Une capacité non prouvée est `UNVERIFIED`. Aucune déclaration de production-ready ne découle de cette seule architecture.

Pour la séquence d'utilisation, voir [le protocole](KERNEL_EXECUTION_PROTOCOL.md).
