"""Rendu HTML d'un Evidence Pack — un seul template, sans JS, imprimable.

Le rendu HTML n'est PAS canonique (whitespace, ordre attributs HTML)
mais reste déterministe : même payload → même HTML pour faciliter le
contrôle visuel par un CAC. Le HTML lui-même n'entre PAS dans le calcul
du `pack_hash` (seul le JSON canonical compte) — le HTML est un rendu
de présentation qui peut évoluer indépendamment.
"""

from __future__ import annotations

import html
from typing import Any


def _escape(value: Any) -> str:
    """HTML-escape neutre — affiche `—` pour None."""
    if value is None:
        return "—"
    return html.escape(str(value), quote=True)


def _row(label: str, value: Any) -> str:
    return f"<tr><th>{_escape(label)}</th><td>{_escape(value)}</td></tr>"


def _section(title: str, body: str) -> str:
    return f"<section><h2>{_escape(title)}</h2>{body}</section>"


def render_html_report(payload: dict[str, Any], pack_hash: str) -> str:
    """Rend un rapport HTML statique du pack."""
    subject = payload.get("subject", {})
    event = payload.get("event", {})
    assessment = payload.get("assessment", {})
    match = payload.get("match", {})
    timeline = payload.get("timeline", [])
    notes = payload.get("notes") or ""

    head_rows = "".join(
        [
            _row("Format version", payload.get("format_version")),
            _row("Subject type", subject.get("type")),
            _row("Subject ID", subject.get("id")),
            _row("Pack hash (SHA-256)", pack_hash),
            _row("Engine version", assessment.get("engine_version")),
            _row("Domain", assessment.get("domain")),
            _row("Assessed at", assessment.get("assessed_at")),
        ]
    )

    event_rows = "".join(
        [
            _row("Event ID", event.get("event_id")),
            _row("Source", event.get("source")),
            _row("Creditor ICS", event.get("creditor_ics")),
            _row("Creditor (raw name)", event.get("creditor_name_raw")),
            _row("RUM", event.get("rum")),
            _row("Amount (cents)", event.get("amount_cents")),
            _row("Currency", event.get("currency")),
            _row("Booking date", event.get("booking_date")),
            _row("Due date", event.get("due_date")),
            _row("Debtor IBAN fingerprint", event.get("debtor_iban_fingerprint")),
            _row("Matched mandate", event.get("matched_mandate_id")),
        ]
    )

    decision = assessment.get("decision")
    level = assessment.get("level")
    score = assessment.get("score")
    decision_block = (
        f"<p class='decision level-{_escape(level)}'>"
        f"<strong>Décision : {_escape(decision)}</strong> · "
        f"score {_escape(score)}/100 · niveau {_escape(level)}"
        "</p>"
    )

    signals = assessment.get("signals", [])
    signals_html = "".join(
        [
            (
                "<li class='signal sev-"
                + _escape(s.get("severity"))
                + "'>"
                + f"<strong>[{_escape(s.get('code'))}] {_escape(s.get('title'))}</strong>"
                + f" <span class='score'>+{_escape(s.get('score'))}</span>"
                + f"<div class='msg'>{_escape(s.get('message'))}</div>"
                + "</li>"
            )
            for s in signals
        ]
    )

    mandate = match.get("mandate") or {}
    match_block = (
        _row("Matched", match.get("matched"))
        + _row("Mandate ID", mandate.get("mandate_id"))
        + _row("Mandate status", mandate.get("status"))
        + _row("RUM", mandate.get("rum"))
        + _row("Max amount (cents)", mandate.get("max_amount_cents"))
        + _row("Warnings", ", ".join(match.get("warnings", [])) or "—")
        + _row("Inactive candidates", len(match.get("candidates_inactive", [])))
    )

    timeline_rows = "".join(
        f"<li><code>{_escape(e.get('kind'))}</code> · "
        f"{_escape(e.get('at'))} · seq {_escape(e.get('seq'))} · "
        f"hash {_escape((e.get('hash') or '')[:16])}…</li>"
        for e in timeline
    )

    style = """
<style>
:root{font-family:system-ui,-apple-system,sans-serif;line-height:1.5;color:#111}
body{max-width:880px;margin:32px auto;padding:0 16px;background:#fafafa}
h1{font-size:1.5rem;margin-bottom:0}
h1+.subtitle{color:#666;font-size:.9rem;margin-top:.25rem}
section{background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:16px;margin:16px 0}
table{width:100%;border-collapse:collapse;font-size:.9rem}
th{text-align:left;padding:4px 8px;font-weight:600;width:35%;color:#444;background:#f4f4f5}
td{padding:4px 8px;border-bottom:1px solid #f1f5f9;word-break:break-word}
.decision{padding:8px 12px;border-radius:6px;font-size:1rem}
.level-CRITICAL{background:#fee2e2;color:#991b1b}
.level-HIGH{background:#ffedd5;color:#9a3412}
.level-MEDIUM{background:#fef3c7;color:#92400e}
.level-LOW{background:#dcfce7;color:#166534}
ul.signals{list-style:none;padding-left:0}
.signal{padding:8px 12px;margin:6px 0;border-left:4px solid #999;background:#f9fafb;border-radius:4px}
.signal.sev-critical{border-color:#dc2626;background:#fef2f2}
.signal.sev-high{border-color:#ea580c;background:#fff7ed}
.signal.sev-medium{border-color:#d97706;background:#fefce8}
.signal.sev-low{border-color:#16a34a;background:#f0fdf4}
.signal .score{color:#666;font-size:.85rem;margin-left:4px}
.signal .msg{color:#374151;margin-top:4px;font-size:.9rem}
code{font-family:ui-monospace,Menlo,monospace;font-size:.85rem;background:#f3f4f6;padding:1px 4px;border-radius:3px}
.timeline{list-style:none;padding-left:0;font-size:.85rem}
footer{color:#9ca3af;font-size:.8rem;margin-top:24px;text-align:center}
</style>
"""

    return (
        "<!doctype html>\n<html lang='fr'><head><meta charset='utf-8'>"
        f"<title>Evidence Pack — {_escape(subject.get('id'))}</title>"
        f"{style}</head><body>"
        f"<h1>Evidence Pack</h1>"
        f"<div class='subtitle'>Sujet {_escape(subject.get('type'))} · "
        f"ID {_escape(subject.get('id'))}</div>"
        + _section("Métadonnées", f"<table>{head_rows}</table>")
        + _section("Décision", decision_block)
        + _section(
            "Signaux de risque",
            f"<ul class='signals'>{signals_html}</ul>"
            if signals
            else "<p>Aucun signal — décision ALLOW.</p>",
        )
        + _section("Événement source", f"<table>{event_rows}</table>")
        + _section("Appariement mandat", f"<table>{match_block}</table>")
        + (
            _section("Timeline audit", f"<ul class='timeline'>{timeline_rows}</ul>")
            if timeline
            else ""
        )
        + (_section("Notes", f"<p>{_escape(notes)}</p>") if notes else "")
        + f"<footer>Pack hash : <code>{_escape(pack_hash)}</code></footer>"
        "</body></html>"
    )
