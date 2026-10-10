"""Human-facing read-only BUILD/RUN status, derived from a current cycle."""
from __future__ import annotations

from collections import Counter
from html import escape


def render(cycle, discovery=None):
    def x(value):
        return escape(str(value), quote=True)

    counts = Counter(t["state"] for t in cycle["tasks"])
    summary = " ".join(f"<span class='pill'>{x(k)}: {v}</span>" for k, v in sorted(counts.items()))
    tasks = "".join("<tr><td>" + x(t["resource"]) + "</td><td>" + x(t["need"]) +
                    "</td><td>" + x(t["state"]) + "</td><td>" + x(t["due"]) + "</td></tr>"
                    for t in cycle["tasks"])
    routes = "".join("<tr><td>" + x(r["id"]) + "</td><td>" + x(r["mode"]) +
                     "</td><td>" + x(r["state"]) + "</td><td>" + x(", ".join(r["required_t"])) +
                     "</td></tr>" for r in cycle["routes"])
    found = "" if discovery is None else "".join(
        "<tr><td>" + x(r["kind"]) + "</td><td>" + x(r["status"]) + "</td><td>" +
        x(", ".join(r["paths"][:5])) + "</td></tr>" for r in discovery["categories"])
    inventory = ("<h2>Contrôles repérés</h2><table><tr><th>Type</th><th>État</th><th>Exemples</th></tr>"
                 + found + "</table>") if discovery is not None else ""
    return ("<!doctype html><html lang='fr'><meta charset='utf-8'><meta name='viewport' "
            "content='width=device-width, initial-scale=1'><title>Standard · BUILD/RUN</title>"
            "<style>body{font:16px system-ui,sans-serif;max-width:1100px;margin:3rem auto;padding:0 1rem;"
            "color:#12232c;background:#f7f9fa}header,section{background:white;padding:1.5rem;"
            "border:1px solid #dce4e8;border-radius:12px;margin-bottom:1rem}h1,h2{margin:0 0 1rem}"
            "table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:.65rem;border-bottom:1px solid #e5eaed}"
            ".pill{display:inline-block;background:#e6eef3;border-radius:1rem;padding:.3rem .7rem;margin:.2rem}"
            "small{color:#54646d}</style><header><h1>Standard · " + x(cycle["mode"]) + "</h1>"
            "<p>État : " + x(cycle["audit_state"]) + " · Loi : " + x(cycle["basis"]["law_digest"]) + "</p>"
            "<p>Obligations et travail : " + summary + "</p><small>La présence d'un outil ne prouve pas sa couverture. "
            "Une tâche ne constitue pas une autorisation.</small></header><section><h2>Travail et décisions</h2>"
            "<table><tr><th>Sujet</th><th>Besoin</th><th>État</th><th>Échéance (ms)</th></tr>"
            + tasks + "</table></section><section><h2>Routes et confiance</h2><table><tr><th>Route</th>"
            "<th>Mode</th><th>État</th><th>T requis</th></tr>" + routes + "</table></section><section>"
            + inventory + "<small>Préfixe : " + x(cycle["basis"]["head"]) + "</small></section></html>")


def render_fault(status):
    """An absent prefix is explicit, never a healthy empty dashboard."""
    reason = escape(str(status.get("reason", "AUDIT_UNAVAILABLE")))
    basis = status.get("basis")
    head = escape(str(basis.get("head"))) if isinstance(basis, dict) else "inconnu"
    return ("<!doctype html><html lang='fr'><meta charset='utf-8'>"
            "<title>Standard · indisponible</title><body><h1>Standard : contrôle indisponible</h1>"
            "<p>État : FAULT. Aucune obligation n'est déclarée résolue.</p><p>Préfixe : "
            + head + "</p><p>Cause : " + reason + "</p></body></html>")
