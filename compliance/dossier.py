"""Compliance dossier: the journal, replayed by the external audit, projected onto ISO 27001, NIS2 and DORA controls.

Outside the TCB. The dossier grants nothing and closes nothing: it reads the verdict that `tcb.audit` derives from
signed entries and tells, control by control, which floor measures are proven, by which signed entry, and which are
gaps. Anyone holding the journal, the genesis pin and a retained checkpoint rebuilds it byte for byte (`verify`)."""
from __future__ import annotations

import hashlib
import html
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tcb import Accountability, Kernel, audit  # noqa: E402
from tcb.canon import canon, digest, parse  # noqa: E402
from tcb.crypto import open_envelope  # noqa: E402
from tcb.floors import FLOORS  # noqa: E402

CATALOG = json.loads((Path(__file__).with_name("catalog.json")).read_text())
FORMAT = "standard-dossier/1"
PROVEN, PARTIAL, GAP = "PROUVÉ", "PARTIEL", "ÉCART"


def rows_of(journal_path) -> list:
    db = sqlite3.connect(f"file:{journal_path}?mode=ro", uri=True)
    try:
        return [parse(raw) for (raw,) in db.execute("SELECT raw FROM entries ORDER BY seq")]
    finally:
        db.close()


def _entries(rows) -> dict:
    """Signed facts by body id: who stated what, when, under which envelope digest."""
    found = {}
    for e in rows:
        kind, body, _, _ = open_envelope(e["envelope"])
        found[body["id"]] = {"seq": e["seq"], "kind": kind, "author": body.get("author"), "at": body.get("at"),
                             "resource": body.get("resource"), "property": body.get("property"),
                             "status": body.get("status"), "signers": [s["keyid"] for s in e["envelope"]["signatures"]],
                             "envelope": "sha256:" + hashlib.sha256(canon(e["envelope"])).hexdigest()}
    return found


def build(rows, *, genesis_pin: str, checkpoints: list, required_at: int) -> dict:
    kernel = Kernel()
    verdict = audit(kernel, Accountability(kernel), rows, genesis_pin=genesis_pin, checkpoints=checkpoints,
                    required_at=required_at)
    facts = _entries(rows)
    verdict = {**verdict, "size": len(rows), "head": digest(rows[-1]) if rows else None}
    targets = {t["id"]: t for t in FLOORS["targets"]}
    measures = {"journal": {"status": PROVEN if verdict["state"] != "FAULT" else GAP, "kind": "journal",
                            "evidence": {"head": verdict["head"], "size": verdict["size"], "replayed": True}}}
    for p in verdict["proven"]:
        if p["target"] in targets:
            measures[p["target"]] = {"status": PROVEN, "evidence": facts.get(p["evidence"], {"id": p["evidence"]})}
    for ob in verdict["open"] + verdict["escalated"]:
        tid = ob.get("target")
        if tid in targets and tid not in measures:
            measures[tid] = {"status": GAP, "needs": ob["needs"], "owner": ob["owner"], "due": ob["due"],
                             "escalated": ob in verdict["escalated"]}
    for tid, t in targets.items():
        m = measures.setdefault(tid, {"status": GAP, "needs": ["observe"]})
        m.update(resource=t["resource"], expect=f'{t["property"]} = {t["expect"]}',
                 kind="attestation" if t["resource"].startswith("org:") else "technique")
    frameworks = []
    for fw in CATALOG["frameworks"]:
        controls, counts = [], {PROVEN: 0, PARTIAL: 0, GAP: 0}
        for c in fw["controls"]:
            done = [m for m in c["measures"] if measures[m]["status"] == PROVEN]
            status = PROVEN if len(done) == len(c["measures"]) else PARTIAL if done else GAP
            counts[status] += 1
            controls.append({**c, "status": status})
        frameworks.append({"id": fw["id"], "name": fw["name"], "scope": fw["scope"], "counts": counts,
                           "controls": controls})
    dossier = {"format": FORMAT, "catalog": digest(CATALOG), "floors": digest(FLOORS), "genesis": genesis_pin,
               "required_at": required_at, "journal": {"head": verdict["head"], "size": verdict["size"],
                                                       "state": verdict["state"], "as_of": verdict["as_of"]},
               "applicability": measures["soa"]["status"], "measures": measures, "frameworks": frameworks}
    return {**dossier, "digest": digest(dossier)}


def verify(dossier: dict, rows, *, checkpoints: list) -> bool:
    """Rebuild from the journal alone; the dossier is genuine only if every byte matches."""
    rebuilt = build(rows, genesis_pin=dossier["genesis"], checkpoints=checkpoints, required_at=dossier["required_at"])
    return canon(rebuilt) == canon(dossier)


def render(dossier: dict) -> str:
    """A self-contained page for auditors; the JSON stays the reference."""
    e = html.escape
    when = lambda ms: __import__("datetime").datetime.utcfromtimestamp(ms / 1000).strftime("%Y-%m-%d %H:%M UTC")
    badge = lambda s: f'<span class="b {"p" if s == PROVEN else "a" if s == PARTIAL else "g"}">{e(s)}</span>'
    parts = []
    for fw in dossier["frameworks"]:
        c = fw["counts"]
        rows = "".join(
            f'<tr><td class="id">{e(x["id"])}</td><td>{e(x["title"])}</td><td>{badge(x["status"])}</td>'
            f'<td class="m">{" ".join(e(m) for m in x["measures"])}</td></tr>' for x in fw["controls"])
        parts.append(f'<section><h2>{e(fw["name"])}</h2><p class="sum">{c[PROVEN]} prouvés · {c[PARTIAL]} partiels · '
                     f'{c[GAP]} écarts — périmètre : {e(fw["scope"])}</p><table><thead><tr><th>Contrôle</th><th>Intitulé'
                     f'</th><th>Statut</th><th>Mesures</th></tr></thead><tbody>{rows}</tbody></table></section>')
    mrows = []
    for mid, m in sorted(dossier["measures"].items()):
        ev = m.get("evidence") or {}
        detail = (f'entrée #{ev.get("seq")} · {e(str(ev.get("author")))} · {when(ev["at"])}' if "at" in ev
                  else f'rejoué : {ev.get("size")} entrées' if ev.get("replayed")
                  else f'manque : {", ".join(m.get("needs", []))}' + (f' · échéance {when(m["due"])}' if "due" in m else ""))
        mrows.append(f'<tr><td class="id">{e(mid)}</td><td>{e(m.get("kind", ""))}</td><td class="m">'
                     f'{e(m.get("resource", "journal"))}</td><td>{badge(m["status"])}</td><td>{detail}</td></tr>')
    j = dossier["journal"]
    return f"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Dossier de conformité</title><style>
:root{{--bg:#fbfaf7;--fg:#1d1b16;--mut:#6b665c;--line:#e4e0d6;--p:#1f7a4d;--a:#a86b00;--g:#b3261e}}
@media (prefers-color-scheme:dark){{:root{{--bg:#16150f;--fg:#ece8dd;--mut:#a39d90;--line:#2e2b23;--p:#5cc48f;--a:#e0a53a;--g:#f08a80}}}}
body{{background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif;margin:0;padding:24px 16px;max-width:1100px;margin:auto}}
h1{{font-size:26px;margin:0 0 4px}}h2{{font-size:18px;margin:32px 0 4px}}.sum,.meta{{color:var(--mut);margin:0 0 12px}}
table{{width:100%;border-collapse:collapse;font-size:14px}}th,td{{text-align:left;padding:6px 8px;border-bottom:1px solid var(--line);vertical-align:top}}
.id{{font-variant-numeric:tabular-nums;white-space:nowrap}}.m{{color:var(--mut);font-family:ui-monospace,monospace;font-size:12px}}
.b{{font-size:12px;font-weight:600;padding:1px 8px;border-radius:10px;border:1px solid currentColor;white-space:nowrap}}
.p{{color:var(--p)}}.a{{color:var(--a)}}.g{{color:var(--g)}}.wrap{{overflow-x:auto}}code{{font-size:12px;word-break:break-all}}
</style></head><body><h1>Dossier de conformité</h1>
<p class="meta">Évalué au {when(dossier["required_at"])} · journal {j["size"]} entrées, état {e(j["state"])} ·
déclaration d'applicabilité : {badge(dossier["applicability"])}</p>
<p class="meta">Tête <code>{e(j["head"])}</code><br>Empreinte du dossier <code>{e(dossier["digest"])}</code></p>
<p class="meta">Chaque statut est dérivé du journal signé, rejoué par l'audit externe. Un statut PROUVÉ est une preuve
technique ou une attestation signée, pas une certification.</p>
<section><h2>Mesures</h2><div class="wrap"><table><thead><tr><th>Mesure</th><th>Type</th><th>Ressource</th><th>Statut</th>
<th>Preuve</th></tr></thead><tbody>{"".join(mrows)}</tbody></table></div></section>
{"".join(f'<div class="wrap">{p}</div>' for p in parts)}</body></html>"""


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(prog="python -m compliance")
    ap.add_argument("command", choices=["build", "verify"])
    ap.add_argument("--journal", required=True)
    ap.add_argument("--checkpoints", required=True, help="JSON list of retained {size, head} pins")
    ap.add_argument("--genesis")
    ap.add_argument("--at", type=int)
    ap.add_argument("--dossier", default="dossier.json")
    ap.add_argument("--html")
    a = ap.parse_args(argv)
    rows, pins = rows_of(a.journal), json.loads(Path(a.checkpoints).read_text())
    if a.command == "build":
        d = build(rows, genesis_pin=a.genesis, checkpoints=pins, required_at=a.at)
        Path(a.dossier).write_text(json.dumps(d, ensure_ascii=False, indent=1))
        if a.html:
            Path(a.html).write_text(render(d))
        print(d["digest"])
        return 0
    ok = verify(json.loads(Path(a.dossier).read_text()), rows, checkpoints=pins)
    print("VÉRIFIÉ" if ok else "NON CONFORME AU JOURNAL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
