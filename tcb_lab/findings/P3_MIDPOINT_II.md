# Phase 3 — Midpoint II : interprétation des 31 expériences approfondies

**Observation source :** [run GitHub Actions #82, ID 37954259498](https://github.com/ichamafif-svg/NEW/actions/runs/37954259498), job adversarial `113900617836` et sortie de trois programmes : `p3_depth_proof.py` (7), `p3_depth_effect.py` (8), `p3_depth_autonomy.py` (16). Registre CI [issue #2](https://github.com/ichamafif-svg/NEW/issues/2). **Ne pas redéfinir le scope ni l'abstraction en phase 3.**

## Résumé des observations : un vert de CI n'est pas un verdict scientifique

- **Preuves 7/7 exécutées :** 4 refus observés et 3 admissions selon les attributs ; une preuve avec drapeau de vérité externe faux est acceptée quand le signataire, le sujet et le niveau satisfont les critères. Le drapeau de vérité n'est jamais signé/transmis ; la TCB **ne peut donc pas le juger**.
- **Effets 8/8 exécutés :** réponse `ack_lost` ou `unknown` → `executed=unknown`, dette `reconcile` ; `ok` → dette `proof` ; `failed` → pas de dette liée à l'intent dans cette fixture. Tous les scénarios font **un appel simulé** au port. Deuxième redemption refusée avec le motif `HIST.TIME` dans tous les huit cas, ce qui **n'isole pas la propriété anti-double-dispatch** : le test réutilise un temps en arrière après l'écriture par le guard. C'est une **insuffisance de l'oracle de test**, pas une violation démontrée.
- **Maintenance 16/16 exécutées :** dans les **dix** répétitions `found:1` à deux cycles, la dernière trace contient `measuring` + `withdrawn`, `live=true`, et la condition historique `no_live` est **fausse**. Le job CI passe car le test consigne cette divergence comme `OBSERVED`. Trois variantes à trois cycles finissent `live=false` ; deux d'entre elles ne comportent qu'un `withdrawn`, l'autre deux. Sur trois contrôles `none` à deux cycles : deux finissent live, un non live. **Ce n'est pas stable entre répétitions** dans ce banc, même avec le même code.

## A. Preuves : séparer identité, qualification et vérité

| Variante | Décision | Obligation `proof` après | Lecture |
|---|---|---|---|
| `true_exact` | ADMITTED | fermée | contrôle positif |
| `false_exact` | ADMITTED | fermée | même entrée observable pour le kernel (label vérité hors payload) |
| `wrong_subject` | PROV.SUBJECT | ouverte | contrôle de ressource |
| `false_oracle_actor` | CAP.HOLDER | ouverte | contrôle d'identité |
| `claimed_lower_grade` | NIV.CERTIFY | ouverte | niveau de qualification requis |
| `claimed_higher_grade` | ADMITTED | fermée | l'affirmation du niveau seule ne garantit pas vérité physique |
| `future_timestamp` | HIST.AHEAD | ouverte | limite d'horodatage appliquée |

**Conclusion intermédiaire :** le noyau vérifie plusieurs propriétés **internes à la déclaration** (identité, sujet, niveau, temps). L'authenticité d'une affirmation signée **ne donne pas accès à la vérité du monde**. En revanche, la paire `true_exact`/`false_exact` ne constitue **pas** deux messages signés différents : elle démontre une dépendance externe logique, pas une vulnérabilité cryptographique ni une attaque sur la couverture. Les prochaines expériences doivent varier réellement la méthode, le coverage, la source matérielle et le contrat de qualification observable.

## B. Effets : une barrière observée n'est pas forcément celle que nous cherchions

La seconde redemption est refusée dans les huit cas, y compris depuis un autre objet Journal partageant **le même fichier SQLite**, mais avec le code **`HIST.TIME`**, et non un refus spécifique de doublon. Cela signifie que **l'oracle actuel est insuffisant** pour attribuer le résultat au verrou de réservation ou au fencing. Les conclusions « anti-replay démontré » ou « double effet impossible » sont donc interdites.

À approfondir :
1. recalculer une date de deuxième redemption postérieure au vrai dernier événement du journal, pas seulement `t+3` ;
2. vérifier la cause exacte du refus, l'état durable, le nombre de vraies invocations et la possibilité de créer un second token/intent ;
3. comparer `failed` à *absence certifiée d'application* vs *erreur renvoyée après application* ; le harnais actuel emploie un retour littéral `failed`, pas une mesure externe du fournisseur ;
4. ordonnanceur contrôlé des interruptions aux frontières admission, réservation, send, ACK, readback, et ensuite multi-processus/hôtes.

## C. Autonomie : comportement dépendant du chemin, pas encore expliqué

**Dix répétitions à deux cycles avec CI rouge : les dix divergent de l'attente historique.** Après un `withdrawn`, un autre sujet `measuring` est vivant et la branche principale reste inchangée. Trois répétitions à trois cycles finissent sans sujet vivant, mais l'historique de phases n'est pas identique. Les contrôles `none` ont également des issues différentes.

Deux hypothèses concurrentes, non tranchées :
- **H1 :** une nouvelle proposition après retrait est légitime car le gap demeure et l'agent doit poursuivre, tandis que l'assertion « aucun sujet live » est trop stricte ;
- **H2 :** la nouvelle proposition est un retraitement injustifié d'une cible sans changement réel, entraînant churn ou travail concurrent parasite.

Alternatives : dépendance à l'horloge réelle, entrées non épinglées, non-déterminisme des probes, variabilité des timestamps ou absence d'isolation. Il faudra identifier l'identité **et la dette** de chaque sujet, la justification du nouveau `measuring`, le temps écoulé, les obligations/échéances avant et après, puis comparer à l'oracle métier indépendamment de la simple règle historique.

## Priorités expérimentales suivantes, dérivées UNIQUEMENT des observations

**P0-R :** rejouer exactement les dix cycles rouges en capturant `id`, `main SHA`, `target`, `opened/due`, `live`, horloges et raisons de création/retrait ; ajouter témoins « gap supprimé » vs « gap toujours réel ». Comprendre la progression légitime **et** la prévention de boucles.

**P0-E :** refaire les huit répétitions avec temps monotone issu de `w.state["last_at"]`, capturer codes de refus différents, vraies réservations et compteur d'egress ; puis séquences de crash et ACK perdu.

**P0-P :** opposer des preuves **signées et distinctes** dont diffèrent réellement méthode, provenance, couverture, âge et déclaration matérielle ; instrumenter un oracle indépendant simulé et sa propre possibilité de mentir.

## Couverture et profondeur honnêtes

Les 31 cas augmentent le nombre de contrastes locaux, mais **ne démontrent pas D4–D6**. Pour O1, nous avons trouvé une divergence de comportement récurrente ; pour E1 une faiblesse du protocole expérimental ; pour P1 une frontière de confiance explicitement visible. **P3 reste ouverte**, sans choix de concept, d'architecture ou de correction du noyau.
