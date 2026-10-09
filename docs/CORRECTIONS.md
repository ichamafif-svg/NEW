# V6 : corrections vérifiées de la fusion

> Archive historique V6. Les chiffres, statuts de release et interfaces ci-dessous décrivent cette revue, pas le code actif. État courant : [README](../README.md), [M2](M2.md), [TCB](TCB.md) et [validation](../validation/summary.json).

La source jointe est V5 ; aucune V6 antérieure n'a été supposée ou utilisée. La seconde base est notre V0.
Le bilan, les choix et les limites sont dans `ANALYSE-V6.md` ; les résultats dans `validation/summary-v6.json`.

- Veto, dépassement gouverné et k+2 humains de V0 conservés.
- Floors, changement de loi par activation et redevabilité injectée de V5 conservés.
- Toutes les propositions deviennent périmées après changement de loi.
- Capacités et intentions épinglent leurs conditions et contrats d'opération.
- Instances et clôtures OBL épinglent la déclaration : aucune réinterprétation de preuves anciennes.
- Cibles intégralement validées avant admission ; preuves liées à leur définition complète.
- Les écarts existants gardent leur ouverture et ne voient pas leur échéance reculer.
- Le second juge lit les déclarations épinglées ; une corruption des champs compilés du premier n'est pas recopiée.
- Les deux juges produisent le même effet canonique avant l'envoi physique.
- L'envoi reste sous le verrou ; l'attente peut être différée hors verrou sous contrat d'adaptateur de confiance.
- Un audit dépassé est refusé par défaut ; un audit historique est demandé explicitement et étiqueté.
- Une activation est comptabilisée sous sa loi d'origine, avant application des nouvelles cibles.
- Le contrôle des routes respecte types et paramètres répétés, avec un algorithme borné.

Le plafond n'est pas relevé : son dépassement reste un échec du contrôle de release. Les tests fonctionnels
et le contrôle de budget sont séparés afin de ne pas confondre sûreté testée et contrainte de taille satisfaite.

## Alignement de la vision

Vision, frontières et capacités manquantes explicitées dans `docs/VISION.md`. Projection des écarts en travail proposé et revue humaine dans `maintenance/`, sans import par le cœur ni pouvoir de clôture. Six tests supplémentaires, dont une projection réelle de health sans écriture du journal. Aucun changement des sources de la TCB.
