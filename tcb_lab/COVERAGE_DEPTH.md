# P3 — Matrice de profondeur vivante

> **Ce tableau indique le niveau d'expérience disponible, PAS une garantie prouvée.** Aucun harnais distant/fournisseur réel exécuté. Les résultats des nouveaux scripts ne sont pas observés. Échelle : S=entrée/décision ; C=compositions temporelles ; F=pannes ; P=frontière physique ; A=progression autonome. `Coded` signifie seulement qu'un test existe.

| Garanties | S | C | F | P | A | Priorité manquante |
|---|---|---|---|---|---|---|
| G01 Gouvernance quorum | Coded | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | identités physiques, multi-approbations, restauration |
| G02 Restrictions | Coded | Coded | NOT_RUN | NOT_RUN | Coded | fencing global après restriction |
| G03 Loi | Coded | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | changements de loi concomitants aux effets |
| G04 Transitions | Coded | Coded | NOT_RUN | NOT_RUN | Coded | delta et admission à oracle indépendant |
| G05 Signatures | Coded | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | WebAuthn, trust chain, runtime crypto |
| G06 Temps | Coded | Coded | NOT_RUN | NOT_RUN | NOT_RUN | temps réel / attesté / signé divergents |
| G07 Preuves | Coded | Coded | NOT_RUN | NOT_RUN | Coded | method, coverage, false signed observations |
| G08 Obligations | Coded | Coded | NOT_RUN | NOT_RUN | Coded | vie longue et permutations changements de loi |
| G09 Effets | Coded | Coded | Coded | NOT_RUN | Coded | fournisseur réel, exact request, exclusivité |
| G10 Réservations | Coded | Coded | Coded | NOT_RUN | Coded | multi-hôte et crash au départ |
| G11 Historique | Coded | NOT_RUN | Coded | NOT_RUN | NOT_RUN | rollback coordonné et restauration host |
| G12 Second juge | Coded | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | mutations communes et oracle externe |
| G13 Vérité vs preuve | Coded | Coded | NOT_RUN | NOT_RUN | Coded | faux scanner et faux univers |
| G14 Genèse / bootstrap | Coded | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | runtime pin, recovery et réinitialisation |
| G15 Égress privilégié | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | cred audit, permissions provider |
| G16 Autonomie | Coded | Coded | NOT_RUN | NOT_RUN | Coded | long runs, flapping, pannes, escalations |

## Règle de lecture

Chaque cellule ne devient `TESTED_*` qu'avec trace vérifiée et identifiant d'expérience. Un scénario de simulation ne prouve aucune propriété d'un hébergement multi-hôte ni d'un fournisseur réel. Les trous les plus critiques sont P pour G09–G11/G14–G15 et F+A pour G08/G16.

## Fin de phase

Se référer à [P3_EXIT_CRITERIA.md](P3_EXIT_CRITERIA.md). Une absence de scénarios n'est jamais une preuve d'absence de faute. Un refus conservateur dépourvu de chemin d'escalade peut être un défaut de progression, même si safety tient.