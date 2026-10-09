# Revue adversariale de M2 : scripts de reproduction

Chaque tour a été mené par un agent indépendant, qui n'avait pas écrit le code relu. Ses scripts sont conservés tels qu'il les a écrits, contre l'état du code **à ce tour**. Ils ne suivent pas les API actuelles et ne font pas partie de `make test`. Des règles qui en découlent sont testées dans `tests/test_m2_review.py`; cela ne signifie pas que tous les constats et contrats de production sont résolus.

Le contexte de chaque tour est dans `docs/M2.md`, section « Registre des tours ».

| Tour | Code relu | Scripts | Constats |
|---|---|---|---|
| 1 et 1 bis | `0020a26` → `9ae917f` | `round1/` (harness.py et scripts r1 à r8) | 12 puis 6 : PR de fork autonome, journal remplaçable, `.git/config` écrit par le modèle, code tiers près des clés, sondes « OK » faute d'erreur, blocages |
| 2 | `9b1fe50` | `round2/` (scripts r1 à r8) | 12 : l'instrument est contrôlé par le sujet (CI, config de pytest, `# nosec`, octet nul), périmètre calculé sur des noms de fichiers, commit fusionné différent du commit jugé, pannes non isolées, revue liée à un pointeur mutable |

## Exécution

L'environnement de la revue historique ne pouvait pas activer seccomp. Les auteurs avaient donc lancé les scripts sur une copie où `lock_down` était neutralisé. Ce contournement historique n'est pas une procédure de validation de la version actuelle, dont `make check` garde le confinement actif. Les scripts de `round1/` importent `harness.py`, qui est dans le même dossier.

```sh
PYTHONPATH=<copie>:<copie>/tests python3 validation/review-m2/round2/r1_review_binds_wrong_head.py
```
