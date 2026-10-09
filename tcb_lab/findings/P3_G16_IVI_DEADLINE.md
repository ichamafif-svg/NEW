# Campagne IV-I — G16, franchissement de l'échéance à sept jours

**9 octobre 2026 — expérience programmée ; résultats à confirmer.**

L'expérience [p3_ivi_g16_deadline.py](../experiments/p3_ivi_g16_deadline.py) garde un écart `vulns=found:2` et un scénario de réparation refusée par les tests. Elle prélève le `due` de l'obligation canonique `target:vulns` depuis `journal.health`, puis compare deux environnements locaux indépendants :

- Un cycle environ cinq minutes **avant** l'échéance.
- Un cycle environ cinq minutes **après** l'échéance.

Elle mesure séparément la présence de cette obligation dans `open`, `escalated`, `proven`, le nombre total d'escalades et l'activité planifiée. Le dépassement de l'échéance **n'implique pas automatiquement une obligation d'escalade**, sauf si la loi ou les floors la définissent explicitement. La simulation peut aussi rencontrer des limites de validité temporelle des attestations et des mandats : ce serait un résultat `INCONCLUSIVE`, non une réfutation.

**Décision en attente :** comparer les observations avec la sémantique normative exacte du délai et des conditions de progression. Ne pas déclarer G16 prouvée ou réfutée sur une simple absence d'escalade. G08 conserve son constat local IV-H, et le scope/noyau restent inchangés.

[Registre GitHub Actions](https://github.com/ichamafif-svg/NEW/issues/2).

## Statut de clôture fonctionnelle (2026-10-09)

Voir [FUNCTIONAL_BOUNDARY_FREEZE_DECISION.md](../FUNCTIONAL_BOUNDARY_FREEZE_DECISION.md) : **16/16 allocations K/T/U figées conditionnellement**, sans certification des garanties ni du déploiement. Les constatations et limites ci-dessus restent valables comme faits historiques/conditions d'audit ; elles ne constituent plus un blocage de **délimitation du noyau**. La validation physique, les preuves empiriques et les portes de sortie de P3 restent ouvertes ; G08/G16 ne doivent pas provoquer une nouvelle boucle d'audit général du produit.
