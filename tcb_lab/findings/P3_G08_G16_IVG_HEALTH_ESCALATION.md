# IV-G — Identité des lignes health et escalade après échecs (G08/G16)

**9 octobre 2026.** Suite aux [résultats IV-F](P3_G08_G16_IVF_BACKOFF.md), le backoff de 24 h a été distingué d'un abandon définitif : une nouvelle proposition apparaît après 25 h. Le health signale 21 éléments ouverts et 0 escalade durant cette fenêtre, mais ces nombres ne suffisent pas à conclure à une garantie G08 ni à une violation G16.

## Protocole IV-G

[p3_ivg_health_escalation.py](../experiments/p3_ivg_health_escalation.py) exécute deux contrôles sur sept cycles : un temps normal et une simulation avec **deux sauts de 25 heures**, pour chercher les deux reprises après délai. Capture, à chaque cycle :
- le contenu identifiable des entrées `journal.health(...).open` et `.escalated`, avec leur nombre et leurs empreintes affichées ;
- les clés `state["obligations"]`, distinctes des obligations de couverture et conformité du health ;
- les `attempt:failed` signés, leur ressource et leur date ;
- les sujets encore actifs et les actions `lifecycle.plan`.

## Hypothèses opposées

**G08.H1 :** les lignes `health.open` incluent des écarts de floors identifiés et stables, indépendants des propositions retirées. **G08.H2 :** les lignes ouvertes sont une synthèse générique de couverture sans sujet/horloge suffisant pour garantir l'identité stable de dette. Dans les deux cas, la sortie `health` doit être reliée au contrat exact avant de prétendre G08 satisfaite.

**G16.H1 :** les reprises après délai créent des propositions sans résoudre le problème ni escalader ; une borne supplémentaire d'escalade est nécessaire. **G16.H2 :** une escalade existe dans un canal distinct, ou la limite de tentatives n'est pas atteinte. L'expérience observe le journal/health local ; son absence d'escalade ne démontre rien hors de ce périmètre.

## Statut et limites

**Codé, intégré en CI ; résultats non confirmés au moment de la rédaction.** Un test vert signifie traces exploitables, pas preuve de conformité. Fournisseurs simulés ; horloge de simulation. Les garanties G08 et G16 restent `OPEN_SEMANTIC`. Aucune modification du noyau, de la loi ou du scope.

[Registre automatique](https://github.com/ichamafif-svg/NEW/issues/2).
