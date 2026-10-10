"""Bounded client-law authoring in TOML, separate from release floors.

This parses a proposal. Only a signed genesis or a governed law activation can
make its declarations effective; a repository file never changes the journal.
"""
from __future__ import annotations

import tomllib
from pathlib import Path

from hybrid_kernel.core import Kernel
from hybrid_kernel.constitution import LawError
from tcb.canon import digest
from tcb.floors import FLOORS

MAX_SOURCE = 1_048_576


class AuthoringError(ValueError):
    pass


def load_source(path):
    source = Path(path)
    if source.stat().st_size > MAX_SOURCE:
        raise AuthoringError("client law source exceeds the bounded size")
    try:
        client = tomllib.loads(source.read_text(encoding="utf-8"))
        effective = Kernel().load(client)
    except (tomllib.TOMLDecodeError, UnicodeError, LawError, ValueError, TypeError) as exc:
        raise AuthoringError("client law is not accepted by this release: " + str(exc)) from exc
    return client, effective.release, effective.digest


def proposal_text(path):
    client, effective, pinned = load_source(path)
    floor_targets = {t["id"] for t in FLOORS["targets"]}
    floor_ops = set(FLOORS["ops"])
    lines = ["# Standard · proposition de loi client", "",
             f"Source : `{Path(path).as_posix()}`.",
             f"Empreinte de loi effective proposée : `{pinned}`.",
             f"Empreinte de la déclaration client : `{digest(client)}`.",
             "Cette lecture ne l'active pas. Seules la genèse signée ou la procédure "
             "de changement de loi peuvent la rendre effective.", "",
             "## Identités liées aux rôles des floors"]
    lines += [f"- `{role}` → `{identity}`." for role, identity in sorted(client["bindings"].items())]
    lines += ["", "## Exigences ajoutées par le client"]
    additions = [t for t in effective["targets"] if t["id"] not in floor_targets]
    lines += [f"- `{t['id']}` : `{t['resource']}` doit avoir `{t['property']}` = "
              f"`{t['expect']}` ; source(s) : {', '.join(t['sources'])}." for t in additions]
    if not additions:
        lines.append("- Aucune cible supplémentaire.")
    lines += ["", "## Opérations ajoutées"]
    lines += [f"- `{name}` : `{op['resource']}` ; T : {', '.join(op['trusted'])}."
              for name, op in sorted(effective["ops"].items()) if name not in floor_ops]
    if not set(effective["ops"]) - floor_ops:
        lines.append("- Aucune opération supplémentaire.")
    lines += ["", "## Autres déclarations client"]
    for name in ("resources", "instruments", "conditions", "evidence", "discharges"):
        entries = client.get(name, {})
        if entries:
            lines.append(f"- {name} : " + ", ".join(f"`{key}`" for key in sorted(entries)) + ".")
    for item in client.get("obligations", []):
        lines.append(f"- Obligation `{item['id']}` : niveau `{item['level']}`, "
                     f"délai {item['due_ms']} ms ; événement(s) d'ouverture " +
                     ", ".join(f"`{rule['kind']}`" for rule in item["open"]) + ".")
    for section, entries in client.get("tighten", {}).items():
        if entries:
            lines.append(f"- Floors resserrés ({section}) : " +
                         ", ".join(f"`{key}`" for key in sorted(entries)) + ".")
    if lines[-1] == "## Autres déclarations client":
        lines.append("- Aucune.")
    lines += ["", "Toutes ces déclarations ont été validées par le même noyau ; "
              "la loi ne devient active qu'après la procédure signée."]
    return "\n".join(lines) + "\n"
