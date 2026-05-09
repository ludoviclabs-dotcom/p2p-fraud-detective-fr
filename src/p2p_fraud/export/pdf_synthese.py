"""Export PDF stylé — rapport de synthèse P2P Fraud Detective FR.

Génère un PDF institutionnel (palette navy/charcoal/or, Inter, tabular-nums)
via weasyprint + Jinja2. Sections : entête, KPIs, top fournisseurs exposition,
top 10 cases critiques, extrait audit trail, mention démonstrateur.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<style>
  @import url('https://rsms.me/inter/inter.css');

  :root {
    --c-navy-900: #0F1B33;
    --c-navy-700: #1F3A6E;
    --c-navy-500: #3E7CB1;
    --c-charcoal: #1A1F2C;
    --c-slate: #5A6478;
    --c-slate-200: #E1E5EE;
    --c-bg: #FFFFFF;
    --c-bg-muted: #F4F6FA;
    --c-gold: #E5A93A;
    --c-alert: #A23E48;
    --c-ok: #3E7C5A;
    --c-warn: #C97B1F;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    font-family: 'Inter', sans-serif;
    font-size: 10pt;
    color: var(--c-charcoal);
    background: var(--c-bg);
    padding: 2cm;
  }

  /* ── En-tête ── */
  .header {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    border-bottom: 3px solid var(--c-navy-700);
    padding-bottom: 0.6rem;
    margin-bottom: 1.4rem;
  }
  .header-left .surtitle {
    font-size: 7pt;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--c-slate);
  }
  .header-left h1 {
    font-size: 18pt;
    font-weight: 700;
    color: var(--c-navy-900);
    margin-top: 0.2rem;
  }
  .header-right {
    text-align: right;
    font-size: 8pt;
    color: var(--c-slate);
  }
  .ribbon {
    display: inline-block;
    background: var(--c-gold);
    color: var(--c-charcoal);
    font-weight: 700;
    font-size: 7pt;
    padding: 0.2rem 0.6rem;
    border-radius: 3px;
    letter-spacing: 0.05em;
    margin-bottom: 0.3rem;
  }

  /* ── KPIs ── */
  .kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 0.8rem;
    margin-bottom: 1.4rem;
  }
  .kpi-card {
    border: 1px solid var(--c-slate-200);
    border-left: 4px solid var(--c-navy-700);
    border-radius: 5px;
    padding: 0.6rem 0.8rem;
    background: var(--c-bg-muted);
  }
  .kpi-label {
    font-size: 7pt;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--c-slate);
  }
  .kpi-value {
    font-size: 15pt;
    font-weight: 700;
    color: var(--c-navy-900);
    font-variant-numeric: tabular-nums;
    margin-top: 0.2rem;
  }
  .kpi-value.alert { color: var(--c-alert); }

  /* ── Sections ── */
  h2 {
    font-size: 11pt;
    font-weight: 600;
    color: var(--c-navy-700);
    border-bottom: 1px solid var(--c-slate-200);
    padding-bottom: 0.3rem;
    margin: 1.2rem 0 0.7rem;
  }

  /* ── Tables ── */
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 8.5pt;
    font-variant-numeric: tabular-nums;
    margin-bottom: 0.8rem;
  }
  th {
    background: var(--c-navy-700);
    color: #FFFFFF;
    padding: 0.35rem 0.5rem;
    text-align: left;
    font-weight: 600;
    font-size: 7.5pt;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }
  td {
    padding: 0.3rem 0.5rem;
    border-bottom: 1px solid var(--c-slate-200);
    color: var(--c-charcoal);
  }
  tr:nth-child(even) td { background: var(--c-bg-muted); }

  .badge {
    display: inline-block;
    border-radius: 3px;
    padding: 0.1rem 0.35rem;
    font-size: 7pt;
    font-weight: 600;
    color: #fff;
  }
  .badge-critical { background: var(--c-alert); }
  .badge-high { background: var(--c-warn); }
  .badge-medium { background: #9AA3B2; }
  .badge-low { background: var(--c-ok); }

  /* ── Footer ── */
  .footer {
    margin-top: 2rem;
    padding-top: 0.6rem;
    border-top: 1px solid var(--c-slate-200);
    font-size: 7.5pt;
    color: var(--c-slate);
    display: flex;
    justify-content: space-between;
  }

  @page {
    size: A4;
    margin: 1.5cm;
  }
</style>
</head>
<body>

<!-- En-tête -->
<div class="header">
  <div class="header-left">
    <div class="surtitle">Rapport de synthèse d'audit P2P</div>
    <h1>P2P Fraud Detective FR</h1>
  </div>
  <div class="header-right">
    <div class="ribbon">DÉMONSTRATEUR · v{{ version }}</div><br>
    Généré le {{ generated_at }}<br>
    Données : fictives ou sources ouvertes<br>
    <em>Hors production</em>
  </div>
</div>

<!-- KPIs -->
<div class="kpi-grid">
  <div class="kpi-card">
    <div class="kpi-label">Factures analysées</div>
    <div class="kpi-value">{{ n_invoices }}</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Exposition totale</div>
    <div class="kpi-value">{{ exposure_total }}</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Findings critiques</div>
    <div class="kpi-value alert">{{ n_critical }}</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Cases ouverts</div>
    <div class="kpi-value">{{ n_cases_open }}</div>
  </div>
</div>

<!-- Top fournisseurs par exposition -->
<h2>Top fournisseurs par exposition (€)</h2>
{% if vendors_rows %}
<table>
  <thead>
    <tr>
      <th>#</th>
      <th>Fournisseur</th>
      <th>Factures</th>
      <th>Exposition €</th>
      <th>Score max</th>
    </tr>
  </thead>
  <tbody>
    {% for row in vendors_rows %}
    <tr>
      <td>{{ loop.index }}</td>
      <td>{{ row.vendor_name }}</td>
      <td>{{ row.n_invoices }}</td>
      <td>{{ row.exposure_eur }}</td>
      <td>{{ row.max_score }}</td>
    </tr>
    {% endfor %}
  </tbody>
</table>
{% else %}
<p>Aucun finding disponible.</p>
{% endif %}

<!-- Top cases critiques -->
<h2>Top 10 cases — exposition critique</h2>
{% if cases_rows %}
<table>
  <thead>
    <tr>
      <th>Case ID</th>
      <th>Titre</th>
      <th>Sévérité</th>
      <th>Statut</th>
      <th>Exposition €</th>
      <th>Assigné à</th>
    </tr>
  </thead>
  <tbody>
    {% for row in cases_rows %}
    <tr>
      <td>{{ row.case_id }}</td>
      <td>{{ row.title }}</td>
      <td>
        <span class="badge badge-{{ row.severity_css }}">{{ row.severity }}</span>
      </td>
      <td>{{ row.status }}</td>
      <td>{{ row.exposure_eur }}</td>
      <td>{{ row.assignee }}</td>
    </tr>
    {% endfor %}
  </tbody>
</table>
{% else %}
<p>Aucun case enregistré.</p>
{% endif %}

<!-- Extrait audit trail -->
<h2>Extrait piste d'audit (10 dernières entrées)</h2>
{% if audit_rows %}
<table>
  <thead>
    <tr>
      <th>Seq</th>
      <th>Horodatage UTC</th>
      <th>Actor</th>
      <th>Kind</th>
      <th>Payload (extrait)</th>
    </tr>
  </thead>
  <tbody>
    {% for row in audit_rows %}
    <tr>
      <td>{{ row.seq }}</td>
      <td>{{ row.at }}</td>
      <td>{{ row.actor }}</td>
      <td>{{ row.kind }}</td>
      <td>{{ row.payload }}</td>
    </tr>
    {% endfor %}
  </tbody>
</table>
{% else %}
<p>Aucune entrée dans l'audit trail.</p>
{% endif %}

<!-- Footer -->
<div class="footer">
  <span>
    P2P Fraud Detective FR — démonstrateur d'audit P2P/AML ·
    Données fictives ou sources ouvertes · Hors production
  </span>
  <span>
    ISA 240 · AS 2401 · Sapin 2 · LCB-FT · DORA art. 28 · AI Act art. 50
  </span>
</div>

</body>
</html>
"""


def _fmt_eur(value: float | None) -> str:
    if value is None or (isinstance(value, float) and value != value):
        return "—"
    return f"{value:,.0f} €".replace(",", " ")


def _severity_css(severity: str) -> str:
    return severity.lower().replace("_", "-")


def build_pdf(
    *,
    invoices_df: pd.DataFrame,
    findings: list,
    cases: list,
    audit_entries: list,
    version: str = "0.3",
    n_top_vendors: int = 10,
) -> bytes:
    """Génère le PDF stylé et retourne les octets."""
    from jinja2 import BaseLoader, Environment
    from weasyprint import HTML

    generated_at = datetime.now(UTC).strftime("%d/%m/%Y %H:%M UTC")

    # KPIs
    n_invoices = f"{len(invoices_df):,}".replace(",", " ")
    exposure_total_raw = invoices_df["amount"].sum() if "amount" in invoices_df.columns else 0.0
    exposure_total = _fmt_eur(exposure_total_raw)
    n_critical = sum(1 for f in findings if getattr(f.severity, "value", f.severity) in ("CRITICAL", "critical"))

    open_statuses = {"open", "OPEN", "in_progress", "IN_PROGRESS", "escalated", "ESCALATED"}
    n_cases_open = sum(1 for c in cases if getattr(c.status, "value", c.status) in open_statuses)

    # Top vendors by exposure
    vendor_rows = []
    if findings and "vendor_id" in invoices_df.columns and "amount" in invoices_df.columns:
        finding_vids = {getattr(f, "vendor_id", None) for f in findings if getattr(f, "vendor_id", None)}
        sub = invoices_df[invoices_df["vendor_id"].isin(finding_vids)] if finding_vids else invoices_df
        if not sub.empty:
            grp = (
                sub.groupby("vendor_id")
                .agg(
                    n_invoices=("invoice_id", "count"),
                    exposure_eur=("amount", "sum"),
                    vendor_name=("vendor_name", "first") if "vendor_name" in sub.columns else ("vendor_id", "first"),
                )
                .sort_values("exposure_eur", ascending=False)
                .head(n_top_vendors)
                .reset_index()
            )
            for _, row in grp.iterrows():
                vendor_rows.append({
                    "vendor_name": str(row.get("vendor_name", row["vendor_id"]))[:45],
                    "n_invoices": int(row["n_invoices"]),
                    "exposure_eur": _fmt_eur(row["exposure_eur"]),
                    "max_score": "—",
                })

    # Top cases
    cases_rows = []
    sorted_cases = sorted(
        cases,
        key=lambda c: (getattr(c, "exposure_eur", None) or 0),
        reverse=True,
    )[:10]
    for c in sorted_cases:
        cases_rows.append({
            "case_id": str(c.case_id)[:16],
            "title": str(c.title or "—")[:50],
            "severity": str(c.severity),
            "severity_css": _severity_css(str(c.severity)),
            "status": getattr(c.status, "value", str(c.status)),
            "exposure_eur": _fmt_eur(getattr(c, "exposure_eur", None)),
            "assignee": str(c.assignee or "—"),
        })

    # Audit entries (last 10)
    audit_rows = []
    for e in audit_entries[-10:]:
        payload_str = str(e.payload)[:80] if e.payload else "—"
        audit_rows.append({
            "seq": e.seq,
            "at": str(e.at)[:19],
            "actor": str(e.actor)[:20],
            "kind": str(e.kind),
            "payload": payload_str,
        })

    env = Environment(loader=BaseLoader(), autoescape=True)
    template = env.from_string(_HTML_TEMPLATE)
    html_str = template.render(
        version=version,
        generated_at=generated_at,
        n_invoices=n_invoices,
        exposure_total=exposure_total,
        n_critical=n_critical,
        n_cases_open=n_cases_open,
        vendors_rows=vendor_rows,
        cases_rows=cases_rows,
        audit_rows=audit_rows,
    )

    # Nettoyer les caractères de contrôle qui pourraient invalider le HTML
    html_str = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", html_str)
    return HTML(string=html_str).write_pdf()
