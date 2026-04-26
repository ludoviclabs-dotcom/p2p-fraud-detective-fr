"""Export Parquet — schéma stable consommé par le dashboard Power BI.

Le `.pbix` joint dans `powerbi/p2p-fraud-dashboard.pbix` pointe vers ces fichiers.
Le schéma DOIT rester compatible (renommage = casser le rapport).

Trois fichiers produits :
- `invoices.parquet` : factures avec colonnes typées
- `findings.parquet` : long format (1 ligne par Finding)
- `risk_scores.parquet` : score consolidé + breakdown par détecteur
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from p2p_fraud.schema import Finding, RiskScore


def _findings_to_long_dataframe(findings: list[Finding]) -> pd.DataFrame:
    if not findings:
        return pd.DataFrame(
            columns=[
                "invoice_id",
                "detector",
                "signal",
                "severity",
                "rule_id",
                "detected_at",
                "evidence_json",
            ]
        )
    import json

    rows = [
        {
            "invoice_id": f.invoice_id,
            "detector": f.detector,
            "signal": f.signal,
            "severity": f.severity.value,
            "rule_id": f.rule_id,
            "detected_at": f.detected_at,
            "evidence_json": json.dumps(f.evidence, default=str, ensure_ascii=False),
        }
        for f in findings
    ]
    df = pd.DataFrame(rows)
    df["detected_at"] = pd.to_datetime(df["detected_at"])
    return df


def _scores_to_dataframe(scores: dict[str, RiskScore]) -> pd.DataFrame:
    if not scores:
        return pd.DataFrame(columns=["invoice_id", "risk_score", "findings_count"])
    rows = [
        {
            "invoice_id": rs.invoice_id,
            "risk_score": float(rs.score),
            "findings_count": int(rs.findings_count),
            **{f"score_{k}": float(v) for k, v in rs.breakdown.items()},
        }
        for rs in scores.values()
    ]
    return pd.DataFrame(rows).fillna(0)


def export_to_parquet(
    output_dir: Path,
    *,
    invoices: pd.DataFrame,
    findings: list[Finding],
    risk_scores: dict[str, RiskScore],
) -> dict[str, Path]:
    """Écrit les 3 fichiers Parquet et renvoie leurs chemins."""
    output_dir.mkdir(parents=True, exist_ok=True)

    paths: dict[str, Path] = {}

    invoices_path = output_dir / "invoices.parquet"
    invoices.to_parquet(invoices_path, index=False)
    paths["invoices"] = invoices_path

    findings_path = output_dir / "findings.parquet"
    _findings_to_long_dataframe(findings).to_parquet(findings_path, index=False)
    paths["findings"] = findings_path

    scores_path = output_dir / "risk_scores.parquet"
    _scores_to_dataframe(risk_scores).to_parquet(scores_path, index=False)
    paths["risk_scores"] = scores_path

    return paths
