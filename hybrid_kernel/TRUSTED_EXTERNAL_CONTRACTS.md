# TRUSTED_EXTERNAL_CONTRACTS — frontières de confiance effectives

**Statut : contrat conceptuel v1 ; implémentations non attestées.** Les neuf domaines ci-dessous sont des **capacités de confiance**, pas une exigence de neuf microservices. Certains peuvent être regroupés, fournis par l'infrastructure du client ou par un prestataire, **à condition de conserver leurs domaines de défaillance et propriétés vérifiables**. Les dépendances T font partie de la *TCB effective*.

## Critère d'appartenance à T

Un composant est Trusted External s'il peut, par une défaillance ou un contournement, (a) donner un pouvoir interdit, (b) effacer/forger une transition admise, (c) transformer un fait faux en preuve suffisante pour autoriser un effet, ou (d) permettre un effet privilégié hors du chemin gouverné. Un ordonnanceur ou agent qui ne fait que proposer une action n'est pas T ; sa clé de déploiement non contrôlée, elle, le devient.

## Catalogue exhaustif des **contrats fonctionnels** identifiés

| ID | Domaine T | Attestation/garantie attendue à l'interface | Défaillance structurante et réaction |
|---|---|---|---|
| T01 | **Trust anchor & runtime pin** | Release, floors, code, genèse et racine authentiquement épinglés | Substitution de binaire, re-genèse, downgrade : fail closed |
| T02 | **Identity & key custody** | Signature, contrôle de clé, liaison d'identité, distinction physique des humains/témoins | Même personne avec plusieurs identités ; clés compromises : séparation indépendante requise |
| T03 | **Trusted time** | Temps d'énoncé, ancrage attesté et temps de départ distingués, provenance et borne d'incertitude | Horloges contradictoires : pas de gain de privilèges, suspension de l'effet |
| T04 | **Durable ledger & independent pin** | Ordre linéarisable, commit atomique, checkpoints ancrés hors domaine de restauration, reprise exacte | Rollback coordonné : rejeter état non ancré et interrompre effets |
| T05 | **Independent constitutional verifier** | Décision seconde par implémentation et domaine effectivement indépendants selon la loi | Bug commun, même input corrompu : désaccord/indépendance non prouvée = blocage |
| T06 | **Evidence qualification & instruments** | Provenance, méthode, couverture, identité du sujet, fraîcheur, séparation des auteurs/mesures | Fausse mesure signée : la signature prouve la source, non la vérité ; ne pas clore |
| T07 | **Effect guard & privileged egress** | Identité de destination, octets exacts, re-jugement au départ, credentials exclusifs, fencing | Route alternative CI/cloud ou effet modifié : aucun dispatch |
| T08 | **Effect receipts & reconciliation** | Réservation durable, idempotency domain, reçus et readback indépendants, état `unknown` explicite | ACK perdu/appliqué inconnu : ne jamais supposer « non appliqué » |
| T09 | **Progress signal & escalation delivery** | Disponibilité et traçabilité des signaux requis, accusé de livraison d'escalade sous hypothèses d'équité | Agent en panne/scheduler indisponible : dette conservée, livraison non présumée |

**T09 :** le noyau décide *quand* l'escalade est due ; la progression et la notification physiques sont conditionnelles à la disponibilité/fairness externe explicitement assumée. Un monitor sans effet sur les droits peut rester U ; le canal T ne couvre que les propriétés indispensables aux garanties promises.

## Interface standard minimale de chaque contrat

Chaque Trusted External fournit un **enregistrement de capacité et une attestation** contenant :
- `contract_id, provider_id, trust_domain, subject, operation, input_digest, output_digest, issued_at, expires_at, signer, version` ;
- provenance des clés et de l'artefact exécuté, règles de renouvellement, erreur normalisée ;
- statut `VERIFIED / REJECTED / UNAVAILABLE / INDETERMINATE` ; tout état non vérifié échoue fermé pour l'admission sensible ;
- limites de couverture, domaine de défaillance, version de la garantie et preuve d'audit reproductible.

Il s'agit d'un **schéma conceptuel**, pas d'une assertion selon laquelle un outil peut attester honnêtement des faits physiques qu'il ne peut pas connaître. L'instrument de mesure, sa méthode et son domaine d'observation sont dans le contrat, pas déduits d'un champ `verified:true`.

## Regroupement des fournisseurs et risque de défaillance commune

La séparation logique **n'implique pas** l'indépendance physique : un unique compte cloud avec tous les droits peut contrôler T01, T02, T04, T05 et T07 malgré cinq services nommés différemment. Pour chaque installation, fournir un **trust graph** indiquant propriétaires, clés, dépendances, modes de restauration, chemins d'egress, humains, compte de facturation, réseau et runtime. Vérifier les arêtes critiques, non la simple présence de produits.

L'infrastructure existante du client est réutilisable si ses garanties sont réellement suffisantes. Elle ne peut pas affaiblir les floors. Une capacité existante non attestable reste **UNVERIFIED**, même si elle fonctionne sur des cas courants.

## Contrats d'échec transversaux

- Un service T indisponible n'accorde jamais une permission par défaut.
- Une observation authentique mais sans couverture n'est pas une preuve de satisfaction.
- L'externalité d'un composant n'autorise pas une exemption de la TCB effective.
- Une décision K positive **ne suffit pas** à garantir l'effet si les T07/T08 ne sont pas opérationnels.
- Un journal SQLite local et ses propres lignes d'audit ne sont **pas** deux ancrages indépendants.
- Une seconde signature sur le même jugement n'est pas un deuxième vérificateur.
- Un escalade envoyée par un agent ne prouve ni réception ni traitement.

## Obligations de conformité d'une intégration production

Pour chaque T01–T09, documenter `IMPLEMENTED / PARTIAL / UNVERIFIED / NOT_AVAILABLE`, test adversarial, responsable, fournisseur, version, domaine de panne, mécanisme de fail-closed, source de preuve, date de revue. Les écarts critiques sont des **bloqueurs de promotion**, pas des raisons d'élargir automatiquement le noyau. Les responsabilités K/T/U des G01–G16 sont référencées dans [la décision figée](../tcb_lab/FUNCTIONAL_BOUNDARY_FREEZE_DECISION.md).

## État actuel du prototype

`hybrid_kernel/trusted.py` apporte une vérification cryptographique de reçu DSSE et son arrimage à la demande, à la loi et au préfixe ; la propriété réelle de la clé du signataire et la qualité des mesures sont externes. `hybrid_kernel/store.py` fournit une transaction SQLite locale, **sans** ancre indépendante anti-rollback. `hybrid_kernel/core.py` n'applique pas encore les contrats constitutionnels complets. Aucune exclusivité physique d'effet ou seconde implémentation de jugement n'est démontrée. Ne pas qualifier la pile de « production ready ».
