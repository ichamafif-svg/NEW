# IV-D — G08 / G16 : interprétation des traces et contrôle corrigé

**Source primaire :** [GitHub Actions 37964069387](https://github.com/ichamafif-svg/NEW/actions/runs/37964069387), job `113933876609`, sortie JSON de `p3_ivd_g08_g16.py` (4 cas `OBSERVED`). **Tous les cas ont été exécutés, mais OBSERVED n'est pas synonyme de réussite des garanties.**

## Résultats individuels de la première exécution

| Scénario | Nombre de propositions distinctes | Cycles `live` / 20 | Cycles `not live` tandis que signal vulnérabilité = `found:2` | Main modifiée | Clés `state["obligations"]` relevées |
|---|---:|---:|---:|---|---|
| G08-red-20 | 2 | 2/20 | 18 | non | aucune |
| G08-healed-20 | 2 | 2/20 | 3 avant le signal `none` au cycle 6 | non | aucune |
| G16-red-20 | 2 | 2/20 | 18 | non | aucune |
| G16-healthy-20 | 1 | 1/20 | 19 | non | aucune |

**Important :** le dernier scénario était un **faux témoin sain** : `sim.default_test="none"` changeait le verdict du *test runner* et non le signal `sim.measured["vulns"]`, resté `found:2`. Cette expérience **ne permet pas** d'inférer un travail inutile sur un dépôt sain. Le script a été rectifié dans une nouvelle révision pour initialiser le signal vulnérabilités à `none` et désactiver les avis synthétiques de dépendances pour le contrôle ; ne pas mélanger ses futurs résultats avec ceux de ce run.

## G16 — résultat le plus discriminant

Dans les variantes où le scanner signale un écart persistant, **les deux propositions deviennent `withdrawn` aux premiers cycles, puis le simulateur ne conserve aucun sujet actif durant 18 cycles sur 20**. La branche principale est inchangée. Cela infirme l'hypothèse naïve « l'existence d'un gap implique qu'une proposition live existe à chaque cycle ». Ce n'est **pas encore** la preuve d'une violation de G16 : le contrat de liveness conditionnelle n'impose pas nécessairement une nouvelle proposition à chaque cycle et l'expérience ne vérifie pas les canaux d'escalade, la disponibilité réelle des agents, ni la justification des retraits.

**Hypothèses concurrentes :** protection intentionnelle contre le churn et backoff, absence de reprise d'une cible encore éligible, ou escalade externe non capturée. **Attaque suivante :** trace des décisions de planification, des conditions de retry, des raisons de retrait et des escalades, plus oracle de progression bornée et conditions de fairness explicites.

## G08 — non-clôture : objet mal observé

La liste `state.get("obligations",{})` est vide dans ces quatre fixtures. **Ce fait ne démontre pas qu'une obligation constitutionnelle a été effacée** : les propositions ops ne sont pas automatiquement des obligations G08, et l'existence du gap scanner peut se représenter dans d'autres parties du journal ou une couche accountability. Il faudrait associer une même exigence et cible canonique à une `opened`, `due`, `coverage`, puis la suivre après plusieurs changements de proposition et demander une véritable attestation de clôture.

## Statut scientifique après interprétation

- **G08 : OPEN_SEMANTIC.** Instrument de suivi actuel insuffisant pour déduire l'identité et la persistance d'une dette.
- **G16 : OPEN_SEMANTIC**, avec observation concrète de **18 cycles sans sujet live** malgré un signal de dégradation persistant. Progrès/escalade et causes de retrait encore à départager.
- **Témoin sain : INVALID_CONTROL** dans le premier run, et **CORRECTED_NOT_YET_VERIFIED** jusqu'au prochain run contenant l'instrument corrigé.
- **Scope : INCHANGÉ.** Les 14 autres allocations demeurent conditionnelles, non prouvées en production.

Ceci est un résultat de phase 3 : aucune correction du noyau ni hypothèse d'architecture n'est décidée à partir de cette trace.
