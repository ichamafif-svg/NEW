"""Contextual constitutional text for agents, derived only from a pinned law.

This is a read-only explanation. It never compiles permissions or replaces K's
judgment. Missing or mismatched provenance produces no agent instructions.
"""
from __future__ import annotations

from tcb.canon import digest
from tcb.floors import FLOORS


class SurfaceError(ValueError):
    pass


def _text(value):
    if not isinstance(value, (str, int)) or isinstance(value, bool):
        raise SurfaceError("unsupported constitutional value")
    return " ".join(str(value).split()).replace("`", "′")[:256]


def _law(view):
    law, basis = view.get("law"), view.get("basis")
    if (not isinstance(law, dict) or not isinstance(basis, dict)
            or digest(law) != basis.get("law_digest")
            or not isinstance(basis.get("head"), str) or not basis["head"]):
        raise SurfaceError("no current pinned constitutional law")
    return law, basis


def _target(law, *, resource=None, target_id=None):
    matches = [t for t in law.get("targets", []) if
               (target_id is not None and t.get("id") == target_id)
               or (target_id is None and t.get("resource") == resource)]
    if len(matches) != 1:
        raise SurfaceError("a task must name exactly one constitutional target")
    return matches[0]


def _source(target):
    floor = next((t for t in FLOORS["targets"] if t["id"] == target["id"]), None)
    return "floor commun, éventuellement resserré" if floor else "loi client"


def _contract(law, target):
    lines = [f"## Loi applicable · {_text(target['id'])}",
             f"- Origine : {_source(target)}.",
             f"- Sujet exact : `{_text(target['resource'])}` ; propriété : `{_text(target['property'])}`.",
             f"- Résultat exigé : `{_text(target['expect'])}` ; preuve minimale : `{_text(target['min_level'])}`.",
             f"- Fraîcheur maximale : {target['fresh_ms']} ms ; délai de l'écart : {target['due_ms']} ms.",
             f"- Responsable : `{_text(target['owner'])}` ; sources recevables : " +
             ", ".join(f"`{_text(s)}`" for s in target["sources"]) + "."]
    if target.get("coverage"):
        coverage = next((t for t in law["targets"] if t["id"] == target["coverage"]), None)
        if coverage is None:
            raise SurfaceError("coverage contract missing")
        lines.append(f"- Couverture préalable : `{_text(coverage['resource'])}` doit valoir "
                     f"`{_text(coverage['expect'])}`.")
    instrument = law.get("instruments", {}).get(target["property"])
    if instrument:
        lines.append(f"- Instrument requis : `{_text(instrument['method'])}` ; couverture "
                     f"`{_text(instrument['coverage'])}`. Une simple déclaration ne suffit pas.")
    if target.get("repair"):
        op = law.get("ops", {}).get(target["repair"])
        if op is None:
            raise SurfaceError("repair operation missing")
        lines.append(f"- Réparation prévue : `{_text(target['repair'])}` sur "
                     f"`{_text(op['resource'])}` ; T au départ : " +
                     ", ".join(f"`{_text(t)}`" for t in op["trusted"]) + ".")
        lines.append(f"- Profil de l'opération : `{_text(op['profile'])}` ; arguments typés : " +
                     ", ".join(f"`{_text(k)}: {_text(v)}`" for k, v in sorted(op["args"].items())) + ".")
        for name, rule in sorted(law.get("conditions", {}).items()):
            if name.startswith(target["repair"] + "-"):
                atoms = [next(iter(atom.items())) for atom in rule.get("all", [])]
                description = "; ".join(_text(kind) + " (" + ", ".join(_text(v) for v in args) + ")"
                                        for kind, args in atoms)
                lines.append(f"- Condition déclarée `{_text(name)}` : {description}. "
                             "Seule la capacité active détermine si elle s'applique.")
    else:
        lines.append("- Décision humaine requise : aucune réparation automatique déclarée.")
    return lines


def _obligations(law, target, need):
    kinds = ({"intent"} if need in {"build", "repair"} else
             {"observation", "measurement"} if need in {"cover", "observe"} else
             {"evidence", *law.get("evidence", {})} if need == "prove" else set())
    lines = []
    if need == "prove":
        for name, decl in sorted(law.get("evidence", {}).items()):
            discharges = law.get("discharges", {}).get(name, [])
            if discharges:
                lines.append(f"- Preuve `{_text(name)}` : champs " +
                             ", ".join(f"`{_text(k)}: {_text(v)}`" for k, v in sorted(decl["fields"].items())) +
                             "; clôture " + ", ".join(f"`{_text(d['obligation'])}` au niveau "
                                                  f"`{_text(d['min_level'])}`" for d in discharges) + ".")
    for decl in law.get("obligations", []):
        rules = [(part, rule) for part in ("open", "close", "gate") for rule in decl.get(part, [])
                 if rule.get("kind") in kinds and rule.get("op", target.get("repair")) == target.get("repair")]
        if rules:
            lines.append(f"- Obligation de loi `{_text(decl['id'])}` : niveau "
                         f"`{_text(decl['level'])}`, délai {decl['due_ms']} ms, "
                         f"comportement à échéance `{_text(decl['on_due'])}`.")
            for part, rule in rules:
                filters = ", ".join(f"{_text(k)} = {_text(v)}" for k, v in rule.get("where", {}).items())
                lines.append(f"  - {_text(part)} sur `{_text(rule['kind'])}` ; clé "
                             f"`{_text(rule['key'])}`" + (f" ; si {filters}." if filters else "."))
            if decl.get("when"):
                lines.append("  - Condition additionnelle : " + "; ".join(
                    f"{_text(name)} (" + ", ".join(_text(v) for v in args) + ")"
                    for atom in decl["when"]["all"] for name, args in atom.items()) + ".")
    return lines


def _law_map(law):
    """One effective inventory: client declarations and floors share the pin."""
    lines = ["## Lois effectives · floors et client"]
    for target in law["targets"]:
        lines.append(f"- `targets/{_text(target['id'])}` ({_source(target)}) : "
                     f"`{_text(target['resource'])}` exige "
                     f"`{_text(target['property'])}` = `{_text(target['expect'])}`.")
    floor_ops = set(FLOORS["ops"])
    for name, op in sorted(law["ops"].items()):
        source = "floor" if name in floor_ops else "client"
        lines.append(f"- Opération {source} `ops/{_text(name)}` : `{_text(op['resource'])}` ; "
                     "T " + ", ".join(f"`{_text(t)}`" for t in op["trusted"]) + ".")
    for section, name in (("obligations", "obligation"), ("resources", "type de ressource"),
                          ("instruments", "instrument"), ("evidence", "preuve"),
                          ("discharges", "clôture")):
        floor = {i["id"] for i in FLOORS[section]} if section == "obligations" else set(FLOORS.get(section, {}))
        entries = law.get(section, [])
        names = ([i["id"] for i in entries] if section == "obligations" else sorted(entries))
        for identifier in names:
            source = "floor" if identifier in floor else "client"
            lines.append(f"- {name.capitalize()} {source} : "
                         f"`{section}/{_text(identifier)}`.")
    lines.append("Demande `python -m standard context --law SECTION/ID` pour voir "
                 "une déclaration complète de cette loi effective.")
    return lines


def _fields(value, depth=0):
    """Render bounded typed declarations without a JSON document for the agent."""
    if depth > 12:
        raise SurfaceError("constitutional declaration exceeds display depth")
    if isinstance(value, dict):
        lines = []
        for key, child in sorted(value.items()):
            lines.append("  " * depth + f"- `{_text(key)}` :")
            lines.extend(_fields(child, depth + 1))
        return lines
    if isinstance(value, list):
        lines = []
        for index, child in enumerate(value, 1):
            lines.append("  " * depth + f"- élément {index} :")
            lines.extend(_fields(child, depth + 1))
        return lines
    if isinstance(value, bool):
        return ["  " * depth + ("vrai" if value else "faux")]
    if value is None:
        return ["  " * depth + "aucune valeur"]
    return ["  " * depth + f"`{_text(value)}`"]


def render_law(cycle, identifier):
    """Show any exact active floor or client declaration on the same pinned basis."""
    law, basis = _law(cycle)
    if not isinstance(identifier, str) or identifier.count("/") != 1:
        raise SurfaceError("law identity must be SECTION/ID")
    section, name = identifier.split("/")
    if section not in {"targets", "obligations", "ops", "resources", "instruments",
                       "conditions", "evidence", "discharges"}:
        raise SurfaceError("unknown law section")
    declarations = law.get(section, {})
    if isinstance(declarations, list):
        matches = [item for item in declarations if item.get("id") == name]
        if len(matches) != 1:
            raise SurfaceError("unknown or ambiguous law declaration")
        declaration = matches[0]
        floor_ids = {item["id"] for item in FLOORS.get(section, [])}
    else:
        if name not in declarations:
            raise SurfaceError("unknown law declaration")
        declaration = declarations[name]
        floor_ids = set(FLOORS.get(section, {}))
    source = "floor commun, éventuellement resserré" if name in floor_ids else "loi client"
    lines = _heading(basis, cycle["mode"]) + [f"## {section}/{_text(name)}", f"Origine : {source}."]
    lines += _fields(declaration)
    lines += ["", "Cette projection décrit la loi effective ; elle n'accorde aucune capacité."]
    return "\n".join(lines) + "\n"


def _physical_work(cycle):
    lines = ["## Frontière physique de la loi"]
    for item in cycle.get("provisioning_work", []):
        lines.append(f"- Installer une route `{_text(item['need'])}` pour "
                     f"`{_text(item['target'])}` ({_text(item['resource'])}) ; "
                     "T exigés : " + ", ".join(f"`{_text(t)}`" for t in item["required_t"]) + ".")
    for item in cycle.get("qualification_work", []):
        lines.append(f"- Qualifier indépendamment la route `{_text(item['route'])}` ; "
                     "T requis : " + ", ".join(f"`{_text(t)}`" for t in item["required_t"]) + ".")
    if len(lines) == 1:
        lines.append("- Aucun besoin d'installation ou de qualification signalé par cette vue ; "
                     "cela ne certifie pas l'état physique.")
    lines.append("Installer une route ne prouve aucun T : sa qualification doit être indépendante et actuelle.")
    return lines


def _heading(basis, mode):
    return ["# Standard · contexte constitutionnel", "",
            f"Mode : **{_text(mode)}**. Lecture seule : ce texte ne donne aucun droit.",
            f"Préfixe : `{_text(basis['head'])}` ; loi : `{_text(basis['law_digest'])}`.",
            "Toute proposition sera rejugée au préfixe courant par K. Les faits "
            "physiques et les effets exigent les T qualifiés de leur route.", ""]


def render_task(cycle, task_id):
    """Give an agent only its target, debt and qualified route choices."""
    law, basis = _law(cycle)
    task = next((t for t in cycle.get("tasks", []) if t.get("id") == task_id), None)
    if task is None:
        raise SurfaceError("unknown task at this prefix")
    lines = _heading(basis, cycle["mode"])
    lines += [f"## Travail · `{_text(task['id'])}`",
              f"- Besoin : `{_text(task['need'])}` ; état : **{_text(task['state'])}**.",
              f"- Obligation persistante : `{_text(task['obligation'])}` ; échéance : {task['due']} ms."]
    if task["state"] != "READY":
        lines.append("- Aucun départ autonome sur cette tâche tant que sa route reste bloquée ou absente.")
    if task.get("required_t"):
        lines.append("- T exigés par la loi pour ce besoin : " +
                     ", ".join(f"`{_text(t)}`" for t in task["required_t"]) + ".")
    for route in task["routes"]:
        lines.append(f"- Route `{_text(route['id'])}` : {_text(route['state'])} ; T requis : " +
                     (", ".join(f"`{_text(t)}`" for t in route["required_t"]) or "aucun supplémentaire") + ".")
    if task["need"] != "reconcile" and task["state"] != "HUMAN_REVIEW":
        target = _target(law, resource=task["resource"], target_id=task.get("target"))
        lines += [""] + _contract(law, target) + _obligations(law, target, task["need"])
    elif task.get("target"):
        target = _target(law, target_id=task["target"])
        lines += [""] + _contract(law, target)
    lines += ["", "Prépare seulement une proposition pour ce sujet. Le reçu d'effet ne clôt pas l'exigence : "
              "une preuve indépendante et recevable est nécessaire."]
    return "\n".join(lines) + "\n"


def render_overview(cycle):
    """One discoverable entry point; agents request detail for a named task."""
    law, basis = _law(cycle)
    lines = _heading(basis, cycle["mode"])
    lines += ["## Travail courant"]
    for task in cycle.get("tasks", []):
        lines.append(f"- `{_text(task['id'])}` : {_text(task['need'])} sur "
                     f"`{_text(task['resource'])}` · {_text(task['state'])} · échéance {task['due']} ms.")
    if not cycle.get("tasks"):
        lines.append("- Aucun travail projeté à ce préfixe ; cela ne certifie pas le monde extérieur.")
    lines += [""] + _law_map(law) + [""] + _physical_work(cycle)
    lines += ["", "Demande `standard context --task <identifiant>` pour la loi et la route "
              "pertinentes. Une tâche n'accorde aucune capacité."]
    return "\n".join(lines) + "\n"


def render_entry(cycle, discovery=None):
    """A single current, scoped entry for an agent in a maintained repository."""
    _, basis = _law(cycle)
    tasks = cycle.get("tasks", [])
    ready = [task for task in tasks if task["state"] == "READY"]
    if ready:
        # The constitutional projection already orders debt by due and identity.
        lines = [render_task(cycle, ready[0]["id"]).rstrip(), "",
                 "## Suite du travail",
                 "La tâche ci-dessus est la première échéance accessible. "
                 "Une proposition signée doit suivre sa route qualifiée ; une réponse de l'agent "
                 "ne clôt jamais la dette."]
        if len(ready) > 1:
            lines.append(f"{len(ready) - 1} autre(s) tâche(s) prête(s) ; "
                         "demande `python -m standard context --task ID` pour leur loi exacte.")
        lines += [""] + _law_map(cycle["law"]) + [""] + _physical_work(cycle)
    else:
        lines = [render_overview(cycle).rstrip(), "",
                 "## Prochaine décision",
                 "Aucun travail autonome prêt à ce préfixe. Les routes manquantes ou "
                 "la qualification des T demandent une intervention de l'installation."]
    if discovery is not None:
        lines.extend(["", "## Indices du dépôt · non qualifiés"])
        for row in discovery["categories"]:
            if row["paths"]:
                lines.append(f"- {_text(row['kind'])} : " +
                             ", ".join(f"`{_text(path)}`" for path in row["paths"][:5]) + ".")
        lines.append("Ces chemins ne prouvent aucune propriété. Seuls les T qualifiés "
                     "peuvent fournir une preuve recevable.")
    lines.extend(["", f"Loi effective : `{_text(basis['law_digest'])}`. "
                  "Les fichiers locaux de proposition ne la remplacent jamais."])
    return "\n".join(lines) + "\n"


def render_uninstalled(discovery):
    """Repository hints without implying an active constitution or trust."""
    lines = ["# Standard · installation absente", "",
             "Aucune connexion K/T installée n'est disponible dans ce dépôt. "
             "La présence de fichiers ne certifie aucun état et ne permet aucune action autonome.",
             "", "## Indices du dépôt · non qualifiés"]
    for row in discovery["categories"]:
        if row["paths"]:
            lines.append(f"- {_text(row['kind'])} : " +
                         ", ".join(f"`{_text(path)}`" for path in row["paths"][:5]) + ".")
    lines += ["", "Prochaine étape : installer le contrôleur K/T et ses T physiques, "
              "puis renseigner `.standard/agent.toml`."]
    return "\n".join(lines) + "\n"


def render_m2(view, target_id):
    """The historical M2 agent receives the same contextual surface."""
    law, basis = _law(view)
    target = _target(law, target_id=target_id)
    lines = _heading(basis, "RUN") + _contract(law, target) + _obligations(law, target, "repair")
    debt = [o for o in view["work"]["work"] + view["work"]["human"]
            if o.get("target") == target_id]
    lines += ["", "## Écart courant"]
    for ob in debt:
        lines.append(f"- `{_text(ob['obligation'])}` : échéance {ob['due']} ms ; "
                     "besoins " + ", ".join(_text(n) for n in ob.get("needs", [])) + ".")
    if not debt:
        lines.append("- Aucun écart courant attesté pour cette cible au préfixe nommé.")
    gaps = view.get("trust_gaps", [])
    if gaps:
        lines += ["", "La qualification physique des T signalés manque ; "
                  "ce constat ne prouve ni leur présence ni leur absence sur l'installation."]
    lines += ["", "Prépare une proposition. Elle ne devient ni un fait indépendant ni une permission."]
    return "\n".join(lines) + "\n"


def render_m2_overview(view):
    law, basis = _law(view)
    lines = _heading(basis, "RUN") + ["## Exigences actives"]
    for target in law["targets"]:
        lines.append(f"- `{_text(target['id'])}` ({_source(target)}) : "
                     f"`{_text(target['resource'])}` exige `{_text(target['property'])}` "
                     f"= `{_text(target['expect'])}`.")
    lines += ["", "## Qualification physique à établir"]
    for gap in view.get("trust_gaps", []):
        lines.append(f"- `{_text(gap['contract'])}` : {_text(gap['status'])} ; "
                     "qualification indépendante requise.")
    if not view.get("trust_gaps"):
        lines.append("- Aucun écart déclaré dans cet inventaire ; vérifier l'installation en direct.")
    lines += ["", "Chaque agent demande ensuite la vue de sa cible exacte ; ce rapport n'accorde aucun droit."]
    return "\n".join(lines) + "\n"
